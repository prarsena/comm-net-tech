import java.awt.Desktop;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.nio.file.Path;
import java.security.KeyStore;
import java.util.Enumeration;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLServerSocket;
import javax.net.ssl.SSLServerSocketFactory;
import javax.net.ssl.SSLSocket;

public final class PhotoServer {
    private static final int PORT = 8443;
    private static final String KEYSTORE_FILE = "keystore.p12";
    private static final String PASSWORD_ENV = "PHOTO_KEYSTORE_PASSWORD";
    private static final Path OUTPUT_FILE = Path.of("received_from_python.jpg");
    private static final String[] TLS_PROTOCOLS = {"TLSv1.3"};

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
            System.out.println("[*] Waiting for Python client connection over TLS 1.3...");
            try {
                printLocalIpv4Addresses();
            } catch (SocketException exception) {
                System.err.println(
                        "[!] Unable to list local IPv4 addresses: " + exception.getMessage());
            }

            try (SSLSocket socket = (SSLSocket) serverSocket.accept()) {
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

                if (Desktop.isDesktopSupported()
                        && Desktop.getDesktop().isSupported(Desktop.Action.OPEN)) {
                    Desktop.getDesktop().open(OUTPUT_FILE.toFile());
                }
            }
        }
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
