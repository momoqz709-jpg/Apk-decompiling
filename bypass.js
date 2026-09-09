// bypass.js - Universal Android SSL Unpinning Script for Frida
Java.perform(function() {
    console.log("[*] SSL Unpinning Script Loaded");

    // 1. Bypass Standard Android TrustManager
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    
    var TrustManager = Java.registerClass({
        name: 'com.fake.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });

    var TrustManagers = [TrustManager.$new()];
    
    try {
        var context = SSLContext.getInstance('TLS');
        context.init(null, TrustManagers, null);
        console.log("[*] Standard TrustManager bypassed");
    } catch(e) {
        console.log("[-] Standard TrustManager bypass failed: " + e);
    }

    // 2. Bypass OkHttp CertificatePinner (Very common in modern apps)
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, peerCertificates) {
            console.log("[*] OkHttp CertificatePinner bypassed for: " + hostname);
        };
        console.log("[*] OkHttp CertificatePinner hook installed");
    } catch(e) {
        console.log("[-] OkHttp not found or already bypassed");
    }

    // 3. Bypass WebViewClient SSL Errors
    try {
        var WebViewClient = Java.use('android.webkit.WebViewClient');
        WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
            console.log("[*] WebView SSL Error bypassed");
            handler.proceed();
        };
        console.log("[*] WebViewClient hook installed");
    } catch(e) {
        console.log("[-] WebViewClient not found");
    }
    
    // 4. Bypass TrustManagerImpl (Android 7+)
    try {
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            console.log("[*] TrustManagerImpl (Conscrypt) bypassed for: " + host);
            return untrustedChain;
        };
    } catch(e) {
        // Conscrypt not used or already bypassed
    }
});
