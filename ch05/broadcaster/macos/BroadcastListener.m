#import <Cocoa/Cocoa.h>
#import <arpa/inet.h>
#import <dispatch/dispatch.h>
#import <errno.h>
#import <netinet/in.h>
#import <string.h>
#import <sys/socket.h>
#import <unistd.h>

static const uint16_t kListenPort = 17429;
enum { kMaximumDatagramSize = 2048 };

@interface BroadcastAppDelegate : NSObject <NSApplicationDelegate, NSWindowDelegate> {
    dispatch_source_t _readSource;
    NSWindow *_messageWindow;
    NSTextField *_senderField;
    NSTextView *_messageView;
    NSMutableString *_messageLog;
    BOOL _terminating;
}
@end

static BroadcastAppDelegate *gAppDelegate = nil;

@implementation BroadcastAppDelegate

- (void)dealloc {
    [_messageWindow setDelegate:nil];
    [_senderField release];
    [_messageView release];
    [_messageWindow release];
    [_messageLog release];
    [super dealloc];
}

- (void)installApplicationMenu {
    NSMenu *mainMenu = [[[NSMenu alloc] initWithTitle:@""] autorelease];
    NSMenuItem *applicationMenuItem =
        [[[NSMenuItem alloc] initWithTitle:@"" action:nil keyEquivalent:@""] autorelease];
    NSMenu *applicationMenu =
        [[[NSMenu alloc] initWithTitle:@"CS240 Broadcast"] autorelease];
    NSString *processName = [[NSProcessInfo processInfo] processName];
    NSString *quitTitle = [NSString stringWithFormat:@"Quit %@", processName];
    NSMenuItem *quitItem =
        [[[NSMenuItem alloc] initWithTitle:quitTitle
                                    action:@selector(terminate:)
                             keyEquivalent:@"q"] autorelease];

    [applicationMenu addItem:quitItem];
    [mainMenu addItem:applicationMenuItem];
    [mainMenu setSubmenu:applicationMenu forItem:applicationMenuItem];
    [NSApp setMainMenu:mainMenu];
}

- (void)showStartupError:(NSString *)message {
    NSAlert *alert = [[[NSAlert alloc] init] autorelease];
    [alert setMessageText:@"Could not start the UDP listener"];
    [alert setInformativeText:message];
    [alert addButtonWithTitle:@"Quit"];
    [alert runModal];
}

- (BOOL)startListener {
    int socketFD = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (socketFD < 0) {
        [self showStartupError:
            [NSString stringWithFormat:@"socket failed: %s", strerror(errno)]];
        return NO;
    }

    struct sockaddr_in address;
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_port = htons(kListenPort);
    address.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(socketFD, (struct sockaddr *)&address, sizeof(address)) < 0) {
        NSString *errorMessage =
            [NSString stringWithFormat:@"Could not bind UDP port %u: %s",
                                       kListenPort,
                                       strerror(errno)];
        close(socketFD);
        [self showStartupError:errorMessage];
        return NO;
    }

    _readSource = dispatch_source_create(
        DISPATCH_SOURCE_TYPE_READ,
        (uintptr_t)socketFD,
        0,
        dispatch_get_main_queue());
    if (_readSource == nil) {
        close(socketFD);
        [self showStartupError:@"Could not create the UDP socket event source."];
        return NO;
    }

    // Under MRC, __block avoids a source/delegate retain cycle; gAppDelegate keeps the delegate alive.
    __block BroadcastAppDelegate *listener = self;
    dispatch_source_set_event_handler(_readSource, ^{
        [listener readAvailableDatagramsFrom:socketFD];
    });
    dispatch_source_set_cancel_handler(_readSource, ^{
        close(socketFD);
    });
    dispatch_resume(_readSource);
    return YES;
}

- (NSString *)displayableMessageFromData:(const char *)bytes length:(size_t)length {
    NSData *data = [NSData dataWithBytes:bytes length:length];
    NSString *message = [[NSString alloc] initWithData:data
                                               encoding:NSUTF8StringEncoding];
    if (message == nil) {
        message = [[NSString alloc] initWithData:data
                                         encoding:NSISOLatin1StringEncoding];
    }

    NSMutableString *displayable = [[NSMutableString alloc] init];
    NSCharacterSet *controlCharacters = [NSCharacterSet controlCharacterSet];
    for (NSUInteger index = 0; index < [message length]; index++) {
        unichar character = [message characterAtIndex:index];
        if ([controlCharacters characterIsMember:character]) {
            [displayable appendFormat:@"\\u%04x", character];
        } else {
            [displayable appendFormat:@"%C", character];
        }
    }
    [message release];
    return [displayable autorelease];
}

- (void)readAvailableDatagramsFrom:(int)socketFD {
    for (NSUInteger datagramIndex = 0; datagramIndex < 32; datagramIndex++) {
        char buffer[kMaximumDatagramSize];
        struct sockaddr_in senderAddress;
        socklen_t senderLength = sizeof(senderAddress);
        ssize_t byteCount = recvfrom(
            socketFD,
            buffer,
            sizeof(buffer),
            MSG_DONTWAIT,
            (struct sockaddr *)&senderAddress,
            &senderLength);

        if (byteCount < 0) {
            if (errno != EAGAIN && errno != EWOULDBLOCK) {
                NSLog(@"UDP receive failed: %s", strerror(errno));
            }
            return;
        }

        char addressText[INET_ADDRSTRLEN] = "unknown";
        inet_ntop(AF_INET, &senderAddress.sin_addr, addressText, sizeof(addressText));
        NSString *sender = [NSString stringWithFormat:@"%@:%u",
                                                      [NSString stringWithUTF8String:addressText],
                                                      ntohs(senderAddress.sin_port)];
        NSString *message =
            [self displayableMessageFromData:buffer length:(size_t)byteCount];
        [self showMessage:message from:sender];
    }
}

- (void)createMessageWindow {
    NSRect contentRect = NSMakeRect(0, 0, 560, 250);
#if __MAC_OS_X_VERSION_MIN_REQUIRED >= 101200
    NSUInteger styleMask =
        NSWindowStyleMaskTitled |
        NSWindowStyleMaskClosable |
        NSWindowStyleMaskMiniaturizable;
#else
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    NSUInteger styleMask =
        NSTitledWindowMask |
        NSClosableWindowMask |
        NSMiniaturizableWindowMask;
#pragma clang diagnostic pop
#endif
    _messageWindow = [[NSWindow alloc] initWithContentRect:contentRect
                                                 styleMask:styleMask
                                                   backing:NSBackingStoreBuffered
                                                     defer:NO];
    [_messageWindow setTitle:@"CS240 UDP Broadcast"];
    [_messageWindow setReleasedWhenClosed:NO];
    [_messageWindow setDelegate:self];
    [_messageWindow center];

    NSView *contentView = [_messageWindow contentView];
    _senderField = [[NSTextField alloc] initWithFrame:NSMakeRect(20, 207, 520, 24)];
    [_senderField setEditable:NO];
    [_senderField setSelectable:NO];
    [_senderField setBezeled:NO];
    [_senderField setDrawsBackground:NO];
    [_senderField setFont:[NSFont boldSystemFontOfSize:13.0]];
    [contentView addSubview:_senderField];

    NSScrollView *scrollView =
        [[NSScrollView alloc] initWithFrame:NSMakeRect(20, 50, 520, 145)];
    [scrollView setHasVerticalScroller:YES];
    [scrollView setBorderType:NSBezelBorder];

    _messageView = [[NSTextView alloc] initWithFrame:NSMakeRect(0, 0, 500, 140)];
    [_messageView setEditable:NO];
    [_messageView setSelectable:YES];
    [_messageView setFont:[NSFont systemFontOfSize:14.0]];
    [_messageView setHorizontallyResizable:NO];
    [_messageView setVerticallyResizable:YES];
    [[_messageView textContainer] setContainerSize:NSMakeSize(500, CGFLOAT_MAX)];
    [[_messageView textContainer] setWidthTracksTextView:YES];
    [_messageView setString:[_messageLog length] > 0
         ? _messageLog
         : @"Waiting for a UDP broadcast message..."];
    [scrollView setDocumentView:_messageView];
    [contentView addSubview:scrollView];
    [scrollView release];
}

- (void)showMessage:(NSString *)message from:(NSString *)sender {
    if (_terminating) {
        return;
    }
    if ([_messageLog length] > 0) {
        [_messageLog appendString:@"\n"];
    }
    [_messageLog appendFormat:@"%@: %@", sender, message];

    if (_messageWindow == nil) {
        [self createMessageWindow];
    }

    [_senderField setStringValue:sender];
    [_messageView setString:_messageLog];
    [_messageView scrollRangeToVisible:NSMakeRange([[_messageView string] length], 0)];
    [_messageWindow makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    (void)notification;
    [self installApplicationMenu];
    _messageLog = [[NSMutableString alloc] init];
    if (![self startListener]) {
        [NSApp terminate:nil];
        return;
    }
    [self createMessageWindow];
    [_senderField setStringValue:[NSString stringWithFormat:@"Listening on UDP/%u",
                                                            kListenPort]];
    [_messageWindow makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    (void)sender;
    return YES;
}

- (void)windowWillClose:(NSNotification *)notification {
    if ([notification object] == _messageWindow) {
        [_messageWindow setDelegate:nil];
        [_senderField release];
        [_messageView release];
        [_messageWindow release];
        _messageWindow = nil;
        _senderField = nil;
        _messageView = nil;
    }
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    (void)notification;
    _terminating = YES;
    if (_readSource != NULL) {
        dispatch_source_set_event_handler(_readSource, NULL);
        dispatch_source_cancel(_readSource);
#if OS_OBJECT_USE_OBJC
        [_readSource release];
#else
        dispatch_release(_readSource);
#endif
        _readSource = NULL;
    }
}

@end

int main(int argc, const char *argv[]) {
    (void)argc;
    (void)argv;
    @autoreleasepool {
        NSApplication *application = [NSApplication sharedApplication];
        [application setActivationPolicy:NSApplicationActivationPolicyRegular];
        gAppDelegate = [[BroadcastAppDelegate alloc] init];
        [application setDelegate:gAppDelegate];
        [application run];
        [application setDelegate:nil];
        [gAppDelegate release];
        gAppDelegate = nil;
    }
    return 0;
}
