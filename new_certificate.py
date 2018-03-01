#! /usr/bin/env python

import argparse
import json
import requests
import sys

from jsonschema import validate


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--csr',
        default=None,
        dest='csr',
        action='store',
        type=str,
        help='The json file containing the csr.'
    )
    args = parser.parse_args()
    if not args.csr:
        print('You must specify the csr file to use for this new certificate.')
        sys.exit(1)
    return args


def import_csr(filename):
    csr_schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        'type': 'object',
        'properties': {
            'CN': {'type': 'string'},
            'key': {
                'type': 'object',
                'properties': {
                    'algo': {'type': 'string'},
                    'size': {'type': 'number'}
                }
            },
            'names': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'C': {'type': 'string'},
                        'L': {'type': 'string'},
                        'ST': {'type': 'string'},
                        'O': {'type': 'string'},
                        'OU': {'type': 'string'}
                    }
                },
                'hosts': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            }
        },
        'required': ['CN', 'key', 'names', 'hosts']
    }
    with open(filename) as f:
        csr = json.load(f)
    validate(csr, csr_schema)
    return csr


def new_cert(csr, ca_address='localhost'):
    url = 'http://{0}:8888/api/v1/cfssl/newcert'.format(ca_address)
    response = requests.post(url, json={'request': csr})
    return response.json()['result']


def main():
    args = arguments()
    csr = import_csr(args.csr)
    cert = new_cert(csr)

    with open('{0}.csr'.format(csr['CN']), 'w') as f:
        f.write(cert['certificate_request'])
    with open('{0}.pem'.format(csr['CN']), 'w') as f:
        f.write(cert['certificate'])
    with open('{0}-key.pem'.format(csr['CN']), 'w') as f:
        f.write(cert['private_key'])

if __name__ == '__main__':
    main()
