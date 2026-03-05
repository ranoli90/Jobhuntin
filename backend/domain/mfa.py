import pyotp


class MFAManager:
    @staticmethod
    def generate_secret():
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(secret, username, issuer_name):
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, issuer_name=issuer_name
        )

    @staticmethod
    def verify(secret, otp):
        totp = pyotp.TOTP(secret)
        return totp.verify(otp)
