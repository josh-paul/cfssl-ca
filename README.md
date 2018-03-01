# Docker cfssl container and instructions to setup a private Root and Intermediate CA

This creates a small docker container for cfssl (~98MB).

The following instructions show how to create a root and intermediate CA. The root CA materials
should be stored offline and encrypted. Use the intermediate CA materials to issue certificates.
This allows for the replacement of the intermediate materials in the case of compromise without
completely invalidating the certifcate chain at the root level.

This container starts the server on port 8888 and does not enforce any authentication. ANYONE able
to access this port will be able to generate new certificates signed by the Intermediate CA.

# Usage:

* Build the Docker image

```bash
docker build -t cfssl .
```

* Set up your config:

```bash
mkdir ca
bash -c 'cat << EOF > ca/config.json
{
    "signing": {
        "default": {
            "expiry": "8760h",
            "usages": [
                "signing",
                "key encipherment",
                "cert sign",
                "crl sign"
            ]
        },
        "ca_constraint": {
            "is_ca": true,
            "max_path_len":0,
            "max_path_len_zero": true
        }
    }
}
EOF'
```

* Set up your Root CA csr

```bash
mkdir ca/root
bash -c 'cat << EOF > ca/root/root-ca-csr.json
{
    "CN": "My Fun Organization/Service - Root CA",
    "key": {
        "algo": "rsa",
	"size": 4096
    },
    "names": [
        {
            "C":  "US",
            "L":  "Some City",
            "O":  "My Fun Organization",
            "ST": "Some State",
            "OU": "My Group / Service"
        }
    ],
    "ca": {
        "expiry": "87600h"
    }
}
EOF'
```

* Generate the root CA

```bash
docker run --rm -v $PWD:/etc/cfssl cfssl gencert -initca /etc/cfssl/ca/root/root-ca-csr.json | \
docker run -i -v $PWD:/etc/cfssl --entrypoint cfssljson cfssl -bare ca/root/root-ca
```

* Add the root CA config

```bash
bash -c 'cat << EOF > ca/root/root-config.json
{
    "signing": {
        "default": {
            "usages": [
                "digital signature",
                "cert sign",
                "crl sign",
                "signing"
            ],
            "expiry": "43800h",
            "ca_constraint": {
                "is_ca": true,
                "max_path_len":0,
                "max_path_len_zero": true
            }
        }
    }
}
EOF'
```

* Setup Intermediate CA csr

```bash
mkdir ca/intermediate
bash -c 'cat << EOF > ca/intermediate/intermediate-ca-csr.json
{
    "CN": "My Fun Organization/Service - Intermediate CA",
    "key": {
        "algo": "rsa",
	"size": 4096
    },
    "names": [
        {
            "C":  "US",
            "L":  "Some City",
            "O":  "My Fun Organization",
            "ST": "Some State",
            "OU": "My Group / Service"
        }
    ]
}
EOF'
```
* Generate the Intermediate CA

```bash
docker run --rm -v $PWD:/etc/cfssl cfssl gencert -initca /etc/cfssl/ca/intermediate/intermediate-ca-csr.json | \
docker run --rm -i -v $PWD:/etc/cfssl --entrypoint cfssljson cfssl -bare ca/intermediate/intermediate-ca
```

* Sign the Intermediate CA

```bash
docker run --rm -v $PWD:/etc/cfssl cfssl sign -ca /etc/cfssl/ca/root/root-ca.pem -ca-key /etc/cfssl/ca/root/root-ca-key.pem -config /etc/cfssl/ca/root/root-config.json /etc/cfssl/ca/intermediate/intermediate-ca.csr | \
docker run --rm -i -v $PWD:/etc/cfssl --entrypoint cfssljson cfssl -bare ca/intermediate/intermediate-ca
```

* Run the cfssl server for the Intermediate CA to issue certs

```bash
docker run -d --init -p 8888:8888 -v $PWD:/etc/cfssl cfssl serve -address=0.0.0.0 -ca=/etc/cfssl/ca/intermediate/intermediate-ca.pem -ca-key=/etc/cfssl/ca/intermediate/intermediate-ca-key.pem -config=/etc/cfssl/ca/config.json 
```

* Validate the Intermediate CA

```bash
openssl x509 -in ca/intermediate/intermediate-ca.pem -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            36:2a:ce:f8:1f:f0:3e:fe:d9:5e:b6:d3:1f:a2:b9:b9:82:5c:7c:c0
    Signature Algorithm: sha512WithRSAEncryption
        Issuer: C=US, ST=Some State, L=Some City, O=My Fun Organization, OU=My Group / Service, CN=My Fun Organization/Service - Root CA
        Validity
            Not Before: Mar  1 22:49:00 2018 GMT
            Not After : Feb 28 22:49:00 2023 GMT
        Subject: C=US, ST=Some State, L=Some City, O=My Fun Organization, OU=My Group / Service, CN=My Fun Organization/Service - Intermediate CA
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (4096 bit)
```
Note the Signature Issuer is the Root CA, then the Intermediate CA. This is the relationship chain.

* Create a CSR for a site

```bash
bash -c 'cat << EOF > service.json
{
    "CN": "service.organization.foo",
    "key": {
        "algo": "rsa",
        "size": 4096
    },
    "names": [
        {
            "C":  "US",
            "L":  "Some City",
            "O":  "My Fun Organization",
            "ST": "Some State",
            "OU": "My Group / Service"
        }
    ],
    "hosts": [
        "service.organization.foo",
        "api.service.organization.foo"
    ]
}
EOF'
```

* Create new certificate for the site

```bash
pip install -r requirements.txt
./new_certificate.py -c service.json
```

* Validate new certificate

```bash
openssl x509 -in service.organization.foo.pem -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            13:88:a6:1c:bd:b7:6b:42:cd:2a:cc:c6:06:1f:82:31:06:d6:55:e2
    Signature Algorithm: sha512WithRSAEncryption
        Issuer: C=US, ST=Some State, L=Some City, O=My Fun Organization, OU=My Group / Service, CN=My Fun Organization/Service - Intermediate CA
        Validity
            Not Before: Mar  1 22:52:00 2018 GMT
            Not After : Mar  1 22:52:00 2019 GMT
        Subject: C=US, ST=Some State, L=Some City, O=My Fun Organization, OU=My Group / Service, CN=service.organization.foo
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (4096 bit)
```