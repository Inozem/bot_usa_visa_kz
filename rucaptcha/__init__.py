import logging
import time
import typing as ty

import requests

from apps.rucaptcha.exceptions import RuCaptchaRequestError, RuCaptchaResponseError, RuCaptchaTimeoutError

logger = logging.getLogger(__name__)


class RuCaptchaBase:
    base_url = "https://rucaptcha.com"

    def __init__(self, token: str):
        self.token = token

    def post(self, path: str, *args, data: dict, **kwargs) -> dict:
        response = requests.post(f"{self.base_url}/{path}", *args, data=data | {"json": 1}, **kwargs)
        if not response.ok:
            raise RuCaptchaRequestError(f"{response.status_code=}")
        payload = response.json()
        logger.debug(f"sent a request with answer {payload=}")
        if not payload.get("status"):
            raise RuCaptchaResponseError(payload)
        return payload


class RuCaptchaAnswerHolder(RuCaptchaBase):
    def __init__(self, token: str, captcha_id: str):
        super().__init__(token)
        self.captcha_id = captcha_id
        self._last_result = {}

    def _update_result(self) -> dict:
        logger.debug(f"requested update: {self._last_result=}")
        data = {"key": self.token, "action": "get", "id": self.captcha_id}
        self._last_result = self.post("res.php", data=data)
        return self._last_result

    @property
    def _result(self) -> dict:
        if self._last_result.get("status"):
            return self._last_result
        return self._update_result()

    @property
    def ready(self):
        try:
            return bool(self._result.get("status"))
        except RuCaptchaResponseError as err:
            payload = err.args[0]
            if payload.get("request") == "CAPCHA_NOT_READY":
                return False
            raise

    @property
    def answer(self) -> str:
        return self._result.get("request")

    def wait_answer(self, attempts: int = 20, delay: float = 3.0):
        while attempts > 0:
            attempts -= 1
            try:
                return self.answer
            except RuCaptchaResponseError:
                time.sleep(delay)
        raise RuCaptchaTimeoutError


class RuCaptcha(RuCaptchaBase):
    def solve(self, file: ty.IO | str) -> RuCaptchaAnswerHolder:
        method = "base64" if isinstance(file, str) else "post"
        kwargs = {"data": {"key": self.token, "method": method}}
        if method == "base64":
            kwargs["data"]["body"] = file
        else:
            kwargs["files"] = {"file": file}

        payload = self.post("in.php", **kwargs)

        if not payload.get("request"):
            raise RuCaptchaResponseError(payload)

        return RuCaptchaAnswerHolder(token=self.token, captcha_id=payload["request"])

    def get_balance(self) -> float:
        data = {"key": self.token, "action": "getbalance"}
        payload = self.post("res.php", data=data)

        try:
            return round(float(payload["request"]), 2)
        except (KeyError, ValueError):
            raise RuCaptchaResponseError(payload) from None
