class RuCaptchaError(Exception):
    pass


class RuCaptchaRequestError(RuCaptchaError):
    pass


class RuCaptchaResponseError(RuCaptchaError):
    pass


class RuCaptchaTimeoutError(RuCaptchaError):
    pass
