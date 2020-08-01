from datetime import datetime

from sanic.request import Request
from sanic.response import HTTPResponse

from slack_bolt import BoltResponse, AsyncApp, AsyncBoltRequest
from slack_bolt.oauth import AsyncOAuthFlow


def to_async_bolt_request(req: Request) -> AsyncBoltRequest:
    return AsyncBoltRequest(
        body=req.body.decode("utf-8"),
        query=req.query_string,
        headers=req.headers,
    )


def to_sanic_response(bolt_resp: BoltResponse) -> HTTPResponse:
    resp = HTTPResponse(
        status=bolt_resp.status,
        body=bolt_resp.body,
        headers=bolt_resp.first_headers_without_set_cookie(),
    )
    for cookie in bolt_resp.cookies():
        for name, c in cookie.items():
            resp.cookies[name] = c.value
            expire_value = c.get("expires", None)
            if expire_value is not None and expire_value != "":
                expire = datetime.strptime(expire_value, "%a, %d %b %Y %H:%M:%S %Z")
                resp.cookies[name]["expires"] = expire
            resp.cookies[name]["path"] = c.get("path", None)
            resp.cookies[name]["domain"] = c.get("domain", None)
            resp.cookies[name]["max-age"] = c.get("max-age", None)
            resp.cookies[name]["secure"] = True
            resp.cookies[name]["httponly"] = True
    return resp


class AsyncSlackRequestHandler():
    def __init__(self, app: AsyncApp):
        self.app = app

    async def handle(self, req: Request) -> HTTPResponse:
        if req.method == "GET":
            if self.app.oauth_flow is not None:
                oauth_flow: AsyncOAuthFlow = self.app.oauth_flow
                if req.path == oauth_flow.install_path:
                    bolt_resp = await oauth_flow.handle_installation(to_async_bolt_request(req))
                    return to_sanic_response(bolt_resp)
                elif req.path == oauth_flow.redirect_uri_path:
                    bolt_resp = await oauth_flow.handle_callback(to_async_bolt_request(req))
                    return to_sanic_response(bolt_resp)

        elif req.method == "POST":
            bolt_resp = await self.app.async_dispatch(to_async_bolt_request(req))
            return to_sanic_response(bolt_resp)

        return HTTPResponse(
            status=404,
            body="Not found",
        )
