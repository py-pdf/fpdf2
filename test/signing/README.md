Demo certificates origin: https://github.com/m32/endesive/tree/master/examples/ca

Display P12 certificate details:

    python $opt/endesive/examples/cert-info-p12.py certs.p12 1234

Display PEM certificate details:

    python $opt/endesive/examples/cert-info-pem.py demo2_ca.crt.pem 1234
    openssl x509 -text -dates -noout -in demo2_ca.crt.pem
