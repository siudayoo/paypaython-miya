import requests
from uuid import uuid4
import pkce
import random
from typing import NamedTuple
from .solver.core import Solver

class PayPayError(Exception):
    pass
class PayPayLoginError(Exception):
    pass
class PayPayNetWorkError(Exception):
    pass

def generate_vector(r1, r2, r3, precision=8):
    v1 = f"{random.uniform(*r1):.{precision}f}"
    v2 = f"{random.uniform(*r2):.{precision}f}"
    v3 = f"{random.uniform(*r3):.{precision}f}"
    return f"{v1}_{v2}_{v3}"

def generate_device_state():
    # ... (PayPaython-mobileのgenerate_device_stateロジックそのまま)
    device_orientation = generate_vector((2.2, 2.6), (-0.2, -0.05), (-0.05, 0.1))
    device_orientation_2 = generate_vector((2.0, 2.6), (-0.2, -0.05), (-0.05, 0.2))
    device_rotation = generate_vector((-0.8, -0.6), (0.65, 0.8), (-0.12, -0.04))
    device_rotation_2 = generate_vector((-0.85, -0.4), (0.53, 0.9), (-0.15, -0.03))
    device_acceleration = generate_vector((-0.35, 0.0), (-0.01, 0.3), (-0.1, 0.1))
    device_acceleration_2 = generate_vector((0.01, 0.04), (-0.04, 0.09), (-0.03, 0.1))
    
    class DeviceHeaders(NamedTuple):
        device_orientation: str
        device_orientation_2: str
        device_rotation: str
        device_rotation_2: str
        device_acceleration: str
        device_acceleration_2: str

    return DeviceHeaders(
        device_orientation, device_orientation_2,
        device_rotation, device_rotation_2,
        device_acceleration, device_acceleration_2
    )

def update_header_device_state(headers:dict):
    device_state = generate_device_state()
    headers["Device-Orientation"] = device_state.device_orientation
    headers["Device-Orientation-2"] = device_state.device_orientation_2
    headers["Device-Rotation"] = device_state.device_rotation
    headers["Device-Rotation-2"] = device_state.device_rotation_2
    headers["Device-Acceleration"] = device_state.device_acceleration
    headers["Device-Acceleration-2"] = device_state.device_acceleration_2
    return headers

class PayPay():
    def __init__(self, phone:str=None, password:str=None, device_uuid:str=None, client_uuid:str=str(uuid4()), access_token:str=None, proxy=None):
        if phone and "-" in phone:
            phone=phone.replace("-","")

        self.session = requests.Session()
        
        # ---------------------------------------------------------
        # Solver統合部分
        # ---------------------------------------------------------
        try:
            solver_proxy = None
            if isinstance(proxy, str):
                solver_proxy = proxy
            elif isinstance(proxy, dict) and "https" in proxy:
                solver_proxy = proxy["https"]

            self.solver = Solver(proxy=solver_proxy)
            self.waf_token = self.solver.get_token()
            
            if self.waf_token:
                self.session.cookies.set("aws-waf-token", self.waf_token, domain="www.paypay.ne.jp")
            else:
                print("Warning: Failed to solve AWS WAF challenge.")
        except Exception as e:
            print(f"Warning: WAF Solver exception: {e}")
        # ---------------------------------------------------------

        if device_uuid:
            self.device_uuid=device_uuid
        else:
            self.device_uuid=str(uuid4())
            
        self.client_uuid=client_uuid

        if isinstance(proxy, str):
            if not "http" in proxy:
                proxy = "http://" + proxy
            self.proxy={"https":proxy,"http":proxy}
        elif isinstance(proxy, dict):
            self.proxy=proxy
        else:
            self.proxy=proxy

        self.params={"payPayLang":"ja"}
        self.version="5.11.1" 
        device_state = generate_device_state()
        self.headers = {
            "Accept": "*/*",
            "Accept-Charset": "UTF-8",
            "Accept-Encoding": "gzip",
            "Client-Mode": "NORMAL",
            "Client-OS-Release-Version": "10",
            "Client-OS-Type": "ANDROID",
            "Client-OS-Version": "29.0.0",
            "Client-Type": "PAYPAYAPP",
            "Client-UUID": self.client_uuid,
            "Client-Version": self.version,
            "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Device-Acceleration": device_state.device_acceleration,
            "Device-Acceleration-2": device_state.device_acceleration_2,
            "Device-Brand-Name": "KDDI",
            "Device-Hardware-Name": "qcom",
            "Device-In-Call": "false",
            "Device-Lock-App-Setting": "false",
            "Device-Lock-Type": "NONE",
            "Device-Manufacturer-Name": "samsung",
            "Device-Name": "SCV38",
            "Device-Orientation": device_state.device_orientation,
            "Device-Orientation-2": device_state.device_orientation_2,
            "Device-Rotation": device_state.device_rotation,
            "Device-Rotation-2": device_state.device_rotation_2,
            "Device-UUID": self.device_uuid,
            "Host": "app4.paypay.ne.jp",
            "Is-Emulator": "false",
            "Network-Status": "WIFI",
            "System-Locale": "ja",
            "Timezone": "Asia/Tokyo",
            "User-Agent": f"PaypayApp/{self.version} Android10"
        }

        if access_token:
            self.access_token=access_token
            self.headers["Authorization"]=f"Bearer {self.access_token}"
            self.headers["content-type"]="application/json"

        elif phone:
            self.access_token=None
            self.refresh_token=None
            self.code_verifier, self.code_challenge = pkce.generate_pkce_pair(43)

            # ログインフローの実行
            self._execute_login(phone, password)

    def _execute_login(self, phone, password):
        # PayPaython-mobileのログインロジックをここに移動・統合
        # WAFトークンがあれば通過できる可能性が高いが、失敗時はtls_clientでのログインが必要かもしれない
        payload = {
            "clientId": "pay2-mobile-app-client",
            "clientAppVersion": self.version,
            "clientOsVersion": "29.0.0",
            "clientOsType": "ANDROID",
            "redirectUri": "paypay://oauth2/callback",
            "responseType": "code",
            "state": pkce.generate_code_verifier(43),
            "codeChallenge": self.code_challenge,
            "codeChallengeMethod": "S256",
            "scope": "REGULAR",
            "tokenVersion": "v2",
            "prompt": "",
            "uiLocales": "ja"
        }
        # ... 以下、PayPaython-mobileのログイン処理を記述 ...
        # 注意: 既存コードの長いログインロジックをここに貼り付けてください。
        # 変更点としては、すべての self.session.post/get 呼び出しは
        # __init__ でセットされた WAF Cookie を自動的に使用します。
        
        # 簡略化のため、ログインの最初のステップだけ記載します
        par = self.session.post("https://app4.paypay.ne.jp/bff/v2/oauth2/par?payPayLang=ja", headers=self.headers, data=payload, proxies=self.proxy)
        try:
            par = par.json()
        except:
            raise PayPayNetWorkError("日本以外からは接続できません")
            
        if par["header"]["resultCode"] != "S0000":
            raise PayPayLoginError(par)
        
        # ... 以降の処理 (authorize, sign-in, token取得) をPayPaython-mobileから移植 ...
        # ... WAFがCookieにあれば、authorize/sign-in もrequestsで通るはずです ...

    # ----------------------------------------------------
    # 以下、PayPaython-mobileのメソッド群 (get_balance, send_moneyなど)
    # これらは変更なしでコピー＆ペーストしてください。
    # ----------------------------------------------------

    def get_balance(self):
        if not self.access_token:
            raise PayPayLoginError("まずはログインしてください")
        
        params = {
            "includePendingBonusLite": "false",
            "includePending": "true",
            "noCache": "true",
            "includeKycInfo": "true",
            "includePayPaySecuritiesInfo": "true",
            "includePointInvestmentInfo": "true",
            "includePayPayBankInfo": "true",
            "includeGiftVoucherInfo": "true",
            "payPayLang": "ja"
        }
        balance=self.session.get("https://app4.paypay.ne.jp/bff/v1/getBalanceInfo",headers=self.headers,params=params,proxies=self.proxy).json()

        if balance["header"]["resultCode"] == "S0001":
            raise PayPayLoginError(balance)
        
        if balance["header"]["resultCode"] != "S0000":
            raise PayPayError(balance)
        
        class GetBalance(NamedTuple):
            money: int
            money_light: int
            all_balance: int
            useable_balance: int
            points: int
            raw: dict
        
        try:
            money=balance["payload"]["walletDetail"]["emoneyBalanceInfo"]["balance"]
        except:
            money=None
            
        money_light=balance["payload"]["walletDetail"]["prepaidBalanceInfo"]["balance"]
        all_balance=balance["payload"]["walletSummary"]["allTotalBalanceInfo"]["balance"]
        useable_balance=balance["payload"]["walletSummary"]["usableBalanceInfoWithoutCashback"]["balance"]
        points=balance["payload"]["walletDetail"]["cashBackBalanceInfo"]["balance"]

        return GetBalance(money,money_light,all_balance,useable_balance,points,balance)

    # ... その他のメソッド (link_check, send_money, etc...) も同様に記述 ...
    
    def alive(self) -> None:
        if not self.access_token:
            raise PayPayLoginError("まずはログインしてください")
        
        alive=self.session.get("https://app4.paypay.ne.jp/bff/v1/getGlobalServiceStatus?payPayLang=en",headers=self.headers,proxies=self.proxy).json()
        if alive["header"]["resultCode"] == "S0001":
            raise PayPayLoginError(alive)
        
        if alive["header"]["resultCode"] != "S0000":
            raise PayPayError(alive)
            
        self.session.post("https://app4.paypay.ne.jp/bff/v3/getHomeDisplayInfo?payPayLang=ja",headers=self.headers,json={"excludeMissionBannerInfoFlag": False,"includeBeginnerFlag": False,"includeSkinInfoFlag": False,"networkStatus": "WIFI"},proxies=self.proxy)
