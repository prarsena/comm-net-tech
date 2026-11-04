import java.awt.Desktop;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.nio.file.Path;
import java.security.KeyStore;
import java.util.Enumeration;
import javax.imageio.ImageIO;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLServerSocket;
import javax.net.ssl.SSLServerSocketFactory;
import javax.net.ssl.SSLSocket;

public final class PhotoServer {
    private enum ImageFilter {
        SEPIA("sepia", "sepia"),
        GRAYSCALE("grayscale", "grayscale"),
        COLOR_NEGATIVE("color negative", "negative");

        private final String label;
        private final String fileSuffix;

        ImageFilter(String label, String fileSuffix) {
            this.label = label;
            this.fileSuffix = fileSuffix;
        }
    }

    private enum FilterResponse {
        YES,
        NO,
        END_OF_INPUT
    }

    private static final int PORT = 8443;
    private static final String KEYSTORE_FILE = "keystore.p12";
    private static final String PASSWORD_ENV = "PHOTO_KEYSTORE_PASSWORD";
    private static final Path OUTPUT_FILE = Path.of("received_from_python.jpg");
    private static final String[] TLS_PROTOCOLS = {"TLSv1.3"};
    private static final BufferedReader CONSOLE_INPUT =
            new BufferedReader(new InputStreamReader(System.in));

    public static void main(String[] args) throws Exception {
        String password = System.getenv(PASSWORD_ENV);
        if (password == null || password.isBlank()) {
            throw new IllegalStateException(
                    "Set PHOTO_KEYSTORE_PASSWORD to the PKCS#12 keystore password.");
        }
        char[] passwordChars = password.toCharArray();

        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        try (FileInputStream input = new FileInputStream(KEYSTORE_FILE)) {
            keyStore.load(input, passwordChars);
        }

        KeyManagerFactory keyManagerFactory =
                KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
        keyManagerFactory.init(keyStore, passwordChars);

        SSLContext sslContext = SSLContext.getInstance("TLSv1.3");
        sslContext.init(keyManagerFactory.getKeyManagers(), null, null);
        SSLServerSocketFactory socketFactory = sslContext.getServerSocketFactory();

        try (SSLServerSocket serverSocket =
                (SSLServerSocket) socketFactory.createServerSocket(PORT)) {
            serverSocket.setEnabledProtocols(TLS_PROTOCOLS);
            System.out.println("[*] Java Photo Ingestion Server listening on port " + PORT + "...");
            try {
                printLocalIpv4Addresses();
            } catch (SocketException exception) {
                System.err.println(
                        "[!] Unable to list local IPv4 addresses: " + exception.getMessage());
            }

            while (true) {
                System.out.println("[*] Waiting for Python client connection over TLS 1.3...");
                SSLSocket socket = (SSLSocket) serverSocket.accept();
                try {
                    handleClient(socket);
                } catch (IOException exception) {
                    System.err.printf(
                            "[!] Client session failed (%s): %s%n",
                            exception.getClass().getSimpleName(), exception.getMessage());
                }
            }
        }
    }

    private static void handleClient(SSLSocket socket) throws IOException {
        try (socket) {
            socket.setEnabledProtocols(TLS_PROTOCOLS);
            socket.startHandshake();

            System.out.println("\n[+] Session established with: " + socket.getRemoteSocketAddress());
            System.out.println("[+] TLS Protocol negotiated: " + socket.getSession().getProtocol());
            System.out.println("[+] TLS Cipher negotiated: " + socket.getSession().getCipherSuite());

            try (DataInputStream input = new DataInputStream(socket.getInputStream())) {
                long totalBytes = Integer.toUnsignedLong(input.readInt());
                if (totalBytes == 0) {
                    throw new IOException("The JPEG payload length must be greater than zero.");
                }
                System.out.printf("[+] Expecting %,d bytes of JPEG data...%n", totalBytes);

                try (FileOutputStream output = new FileOutputStream(OUTPUT_FILE.toFile())) {
                    byte[] buffer = new byte[16_384];
                    long receivedBytes = 0;
                    while (receivedBytes < totalBytes) {
                        int bytesToRead =
                                (int) Math.min(buffer.length, totalBytes - receivedBytes);
                        int bytesRead = input.read(buffer, 0, bytesToRead);
                        if (bytesRead == -1) {
                            throw new EOFException(
                                    "Connection closed after " + receivedBytes
                                            + " of " + totalBytes + " bytes.");
                        }
                        output.write(buffer, 0, bytesRead);
                        receivedBytes += bytesRead;
                        double percent = (receivedBytes * 100.0) / totalBytes;
                        System.out.printf(
                                "\r[+] Received %,d / %,d bytes (%.1f%%)",
                                receivedBytes, totalBytes, percent);
                    }
                }

                System.out.println();
                System.out.println(
                        "[+] Successfully saved decrypted image: "
                                + OUTPUT_FILE.toAbsolutePath());
            }
        }
        openImage(OUTPUT_FILE);
        offerImageFilters();
    }

    private static void offerImageFilters() throws IOException {
        for (ImageFilter filter : ImageFilter.values()) {
            FilterResponse response = askToApplyFilter(filter);
            if (response == FilterResponse.END_OF_INPUT) {
                return;
            }
            if (response == FilterResponse.NO) {
                continue;
            }

            Path editedFile =
                    OUTPUT_FILE.resolveSibling(
                            "received_from_python_" + filter.fileSuffix + ".jpg");
            applyImageFilter(OUTPUT_FILE, editedFile, filter);
            System.out.println(
                    "[+] Applied "
                            + filter.label
                            + " filter and saved: "
                            + editedFile.toAbsolutePath());
            openImage(editedFile);
            return;
        }

        System.out.println("[*] No filter applied; the original image remains unchanged.");
    }

    private static FilterResponse askToApplyFilter(ImageFilter filter) throws IOException {
        System.out.printf(
                "[?] Would you like to apply a %s filter to the image? (y/N): ",
                filter.label);
        System.out.flush();

        String response = CONSOLE_INPUT.readLine();
        if (response == null) {
            System.out.println("[!] No input received; stopping filter selection.");
            return FilterResponse.END_OF_INPUT;
        }

        String normalizedResponse = response.trim();
        if (normalizedResponse.equalsIgnoreCase("y")
                || normalizedResponse.equalsIgnoreCase("yes")) {
            return FilterResponse.YES;
        }
        return FilterResponse.NO;
    }

    private static void applyImageFilter(
            Path inputFile, Path outputFile, ImageFilter filter) throws IOException {
        BufferedImage image = ImageIO.read(inputFile.toFile());
        if (image == null) {
            throw new IOException("Unable to decode image: " + inputFile.toAbsolutePath());
        }

        for (int y = 0; y < image.getHeight(); y++) {
            for (int x = 0; x < image.getWidth(); x++) {
                image.setRGB(x, y, applyFilterToPixel(image.getRGB(x, y), filter));
            }
        }

        if (!ImageIO.write(image, "jpg", outputFile.toFile())) {
            throw new IOException("No JPEG writer is available to save the filtered image.");
        }
    }

    private static int applyFilterToPixel(int rgb, ImageFilter filter) {
        int sourceRed = (rgb >> 16) & 0xFF;
        int sourceGreen = (rgb >> 8) & 0xFF;
        int sourceBlue = rgb & 0xFF;
        int red = sourceRed;
        int green = sourceGreen;
        int blue = sourceBlue;

        switch (filter) {
            case SEPIA:
                red = Math.min(
                        255, (int) (0.393 * sourceRed + 0.769 * sourceGreen + 0.189 * sourceBlue));
                green = Math.min(
                        255, (int) (0.349 * sourceRed + 0.686 * sourceGreen + 0.168 * sourceBlue));
                blue = Math.min(
                        255, (int) (0.272 * sourceRed + 0.534 * sourceGreen + 0.131 * sourceBlue));
                break;
            case GRAYSCALE: {
                int gray = (int) (0.299 * sourceRed + 0.587 * sourceGreen + 0.114 * sourceBlue);
                red = gray;
                green = gray;
                blue = gray;
                break;
            }
            case COLOR_NEGATIVE:
                red = 255 - sourceRed;
                green = 255 - sourceGreen;
                blue = 255 - sourceBlue;
                break;
            default:
                throw new IllegalArgumentException("Unsupported image filter: " + filter);
        }

        return (red << 16) | (green << 8) | blue;
    }

    private static void openImage(Path imageFile) {
        if (Desktop.isDesktopSupported()) {
            Desktop desktop = Desktop.getDesktop();
            if (desktop.isSupported(Desktop.Action.OPEN)) {
                try {
                    desktop.open(imageFile.toFile());
                    return;
                } catch (IOException exception) {
                    System.err.println(
                            "[!] Could not open image with the default application: "
                                    + exception.getMessage());
                }
            }
        }

        if (System.getProperty("os.name").startsWith("Windows")) {
            try {
                new ProcessBuilder(
                        "mspaint.exe", imageFile.toAbsolutePath().toString())
                        .start();
                System.out.println(
                        "[+] Started Paint with " + imageFile.getFileName() + ".");
                return;
            } catch (IOException exception) {
                System.err.println("[!] Could not start Paint: " + exception.getMessage());
            }
        }

        System.err.println(
                "[!] Open the image manually: " + imageFile.toAbsolutePath());
    }

    private static void printLocalIpv4Addresses() throws SocketException {
        System.out.println("[*] Local IPv4 addresses for the Python client (port " + PORT + "):");
        Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
        boolean foundAddress = false;

        while (interfaces != null && interfaces.hasMoreElements()) {
            NetworkInterface networkInterface = interfaces.nextElement();
            if (!networkInterface.isUp() || networkInterface.isLoopback()) {
                continue;
            }

            Enumeration<InetAddress> addresses = networkInterface.getInetAddresses();
            while (addresses.hasMoreElements()) {
                InetAddress address = addresses.nextElement();
                if (!(address instanceof Inet4Address)
                        || address.isAnyLocalAddress()
                        || address.isLoopbackAddress()) {
                    continue;
                }

                System.out.printf(
                        "[*]   %s (%s)%n",
                        address.getHostAddress(), networkInterface.getDisplayName());
                foundAddress = true;
            }
        }

        if (!foundAddress) {
            System.out.println("[!] No active non-loopback IPv4 addresses found.");
        }
    }
}
