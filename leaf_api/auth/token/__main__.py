import sys

from leaf_api.auth.jwt_handler import JWTHandler

handler = JWTHandler(
    public_key_path="leaf_api/auth/public_key.pem",
    private_key_path="leaf_api/auth/keypair.pem"
)

if __name__ == '__main__':
    role = "admin" if len(sys.argv) == 1 else sys.argv[1]
    print(handler.create_token(user_id=role, role=role, exp=3600))

