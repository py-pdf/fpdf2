#!/bin/bash
set -euo pipefail

# ===============================================
# Configuration
# ===============================================
KEY_FILE="private-key.pem"
CRT_FILE="signing-certificate.crt"
P12_FILE="signing-certificate.p12"
CNF_FILE="openssl-ext.cnf"
P12_PASSWORD="fpdf2"
SERIAL_NUMBER=127
DAYS_VALID=3650

# ===============================================
# Step 1: Create OpenSSL config file
# ===============================================
cat > "$CNF_FILE" <<EOF
[ req ]
distinguished_name = req_distinguished_name
x509_extensions = v3_signing
prompt = no

[ req_distinguished_name ]
CN = fpdf2
O = fpdf2
OU = signing testing

[ v3_signing ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
basicConstraints = CA:FALSE
keyUsage = digitalSignature
extendedKeyUsage = emailProtection, clientAuth
subjectAltName = @alt_names
authorityInfoAccess = @aia

[ alt_names ]
email.1 = signer@fpdf2.local

[ aia ]
caIssuers;URI.0 = http://ca.example.com/ca.pem
OCSP;URI.0 = http://ocsp.example.com
EOF

echo "OpenSSL config written to $CNF_FILE"

# ===============================================
# Step 2: Generate RSA private key
# ===============================================
openssl genpkey -algorithm RSA -out "$KEY_FILE"

echo "Private key generated: $KEY_FILE"

# ===============================================
# Step 3: Create self-signed certificate
# ===============================================
openssl req -x509 -new -nodes \
  -key "$KEY_FILE" \
  -days "$DAYS_VALID" \
  -out "$CRT_FILE" \
  -config "$CNF_FILE" \
  -extensions v3_signing \
  -set_serial "$SERIAL_NUMBER"

echo "Self-signed certificate created: $CRT_FILE"

# ===============================================
# Step 4: Generate PKCS#12 bundle for signing with Endesive
# ===============================================
openssl pkcs12 -export \
  -in "$CRT_FILE" \
  -inkey "$KEY_FILE" \
  -out "$P12_FILE" \
  -name "fpdf2" \
  -password pass:"$P12_PASSWORD"

echo "PKCS#12 bundle created: $P12_FILE (password: $P12_PASSWORD)"
