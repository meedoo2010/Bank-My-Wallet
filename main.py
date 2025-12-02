from flet import *
import random
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
from dotenv import load_dotenv
import os
import threading
import time
import webbrowser
import firebase_admin
from firebase_admin import credentials, db
import requests
import tempfile

DB_URL = "https://bank-my-wallet-default-rtdb.asia-southeast1.firebasedatabase.app/bank_my_wallet.json"



class Saver:
    def __init__(self, page):
        self.page = page
        stored = page.client_storage.get("actions")
        if isinstance(stored, dict):
            self.data = stored
        else:
            self.data = {}

    def save(self, key, value):
        self.data[key] = value
        self.page.client_storage.set("actions", self.data)

    def get(self, key, default=None):
        return self.data.get(key, default)



#cred = credentials.Certificate("serviceAccountKey.json")
#
## 2- نبدأ التطبيق
#firebase_admin.initialize_app(cred, {
#    "databaseURL": "https://bank-my-wallet-default-rtdb.asia-southeast1.firebasedatabase.app/"
#})





load_dotenv()

def send_email(to: str, subject: str, body: str):
    sender = os.getenv("EMAIL")
    pwd = os.getenv("PASSWORD")
    
    display_name = "Bank My Wallet"
    
    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = formataddr((str(Header(display_name, "utf-8")), sender))
    msg['To'] = to
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as sender_email:
        sender_email.login(sender, pwd)
        sender_email.sendmail(sender, to, msg.as_string())



def main(page: Page):
    page.title = "Bank My Wallet"
    page.window.width = 390
    page.window.height = 740
    page.window.top = 45
    page.window.left = 570
    page.theme_mode = ThemeMode.LIGHT
    page.scroll = 'auto'
    saver = Saver(page)
    saved_theme = saver.get("theme")
    if saved_theme == "dark":
        page.theme_mode = ThemeMode.DARK



    def add1(e):
        # 1) فحص الخانات الفاضية
        fields = [
            signup_name.value,
            signup_email.value,
            signup_OTP.value,
            signup_phone.value,
            signup_pass.value,
            signup_confirm.value,
            signup_address.value
        ]

        if any(field.strip() == "" for field in fields):
            def close_dialog(ev):
                alert.open = False
                page.update()
            alert = AlertDialog(
                title=Text("Enter what is required"),
                actions=[TextButton("Ok", on_click=close_dialog)],
                actions_alignment=MainAxisAlignment.END,
            )
            page.overlay.append(alert)
            alert.open = True
            page.update()
            return

        # 2) فحص الباسورد
        if signup_pass.value != signup_confirm.value:
            def close_dialog(ev):
                alert.open = False
                page.update()
            alert = AlertDialog(
                title=Text("The password not equal"),
                actions=[TextButton("Ok", on_click=close_dialog)],
                actions_alignment=MainAxisAlignment.END,
            )
            page.overlay.append(alert)
            alert.open = True
            page.update()
            return

        # 3) فحص OTP
        if str(signup_OTP.value) != str(otp_code):
            def close_dialog(ev):
                alert.open = False
                page.update()
            alert = AlertDialog(
                title=Text("OTP mistake"),
                actions=[TextButton("Ok", on_click=close_dialog)],
                actions_alignment=MainAxisAlignment.END,
            )
            page.overlay.append(alert)
            alert.open = True
            page.update()
            return

        # 4) تأكد أن كلمة المرور 8 حروف على الأقل
        if len(signup_pass.value) < 8:
            def close_dialog(ev):
                alert.open = False
                page.update()
            alert = AlertDialog(
                title=Text("Please enter at least 8 characters"),
                actions=[TextButton("Ok", on_click=close_dialog)],
                actions_alignment=MainAxisAlignment.END,
            )
            page.overlay.append(alert)
            alert.open = True
            page.update()
            return

        # 5) إرسال البيانات للـ Firebase عبر requests
        payload = {
            "name": signup_name.value,
            "phone": signup_phone.value,
            "email": signup_email.value,
            "password1": signup_pass.value,
            "password2": signup_confirm.value,
            "address": signup_address.value
        }

        try:
            r = requests.post(DB_URL, json=payload)
            if r.status_code != 200:
                raise Exception(f"Failed to save user. Status code: {r.status_code}")
        except Exception as ex:
            def close_dialog(ev):
                alert.open = False
                page.update()
            alert = AlertDialog(
                title=Text("Error saving data"),
                content=Text(str(ex)),
                actions=[TextButton("Ok", on_click=close_dialog)],
                actions_alignment=MainAxisAlignment.END,
            )
            page.overlay.append(alert)
            alert.open = True
            page.update()
            return

        # بعد الإضافة
        page.go("visa")
        page.update()



    
    
        
        
        
    
    
    
    def route_change(route):
        page.views.clear()

        # الصفحة الرئيسية(2)
        page.views.append(
            View(
                "/",
                [
                    AppBar(title=Text("Bank My Wallet",),
                           center_title=True,
                           bgcolor=Colors.BLACK,
                           color='#E8D04A',
                           actions=[IconButton(Icons.SETTINGS,on_click=lambda _: page.go("setting"))]
                           ),
                    Row([
                        Image(src="register1.gif", width=280),
                    ], alignment=MainAxisAlignment.CENTER),
                    Row([
                        Text("Number of registered customers : 0", size=18, color=Colors.PURPLE),
                    ], alignment=MainAxisAlignment.CENTER),
                    
                    
                    Row(
                        [
                            ElevatedButton(
                                "Login",
                                width=170,
                                style=ButtonStyle(bgcolor="purple", color="white"),
                                on_click=lambda _: page.go("login"),
                            ),
                            ElevatedButton(
                                "Create account",
                                width=170,
                                style=ButtonStyle(bgcolor="purple", color="white"),
                                on_click=lambda _: page.go("signup"),
                            ),
                        ],
                        alignment=MainAxisAlignment.CENTER,
                    ),
                ],
            )
        )
        
        
        def close_alert(a):     
            try:
                a.open = False
            except Exception:
                pass
            page.update()
        
        def user_found(e):
            email_val = (email_field.value or "").strip()
            pass_val = (password_field.value or "").strip()

            if email_val == "" or pass_val == "":
                alert = AlertDialog(
                    title=Text("Please enter email and password"),
                    actions=[TextButton("Ok", on_click=lambda _: close_alert(alert))],
                    actions_alignment=MainAxisAlignment.END
                )
                page.overlay.append(alert)
                alert.open = True
                page.update()
                return

            try:
                r = requests.get(DB_URL)
                if r.status_code != 200:
                    raise Exception(f"Firebase returned status code {r.status_code}")
                users = r.json()
            except Exception as ex:
                alert = AlertDialog(
                    title=Text("Connection error to server"),
                    content=Text(str(ex)),
                    actions=[TextButton("Ok", on_click=lambda _: close_alert(alert))],
                    actions_alignment=MainAxisAlignment.END
                )
                page.overlay.append(alert)
                alert.open = True
                page.update()
                return

            found = False
            if users and isinstance(users, dict):
                for uid, data in users.items():
                    if not isinstance(data, dict):
                        continue
                    if data.get("email") == email_val and data.get("password1") == pass_val:
                        found = True
                        saver.save("current_user_email", email_val)
                        page.go("main1")
                        page.update()
                        break

            if not found:
                alert = AlertDialog(
                    title=Text("Your Email or password is wrong"),
                    actions=[TextButton("Ok", on_click=lambda _: close_alert(alert))]
                )
                page.overlay.append(alert)
                alert.open = True
                page.update()

     
        
        # صفحة تسجيل الدخول
        if page.route == "login":
            email_field = TextField(label="E-mail")
            password_field = TextField(label="Password", password=True, can_reveal_password=True)
            login_button = ElevatedButton(
                "Login",
                width=170,
                style=ButtonStyle(bgcolor="purple", color="white"),
                on_click=user_found,
            )
            go_signup_btn = ElevatedButton(
                "I don't have an account",
                width=170,
                style=ButtonStyle(bgcolor="purple", color="white"),
                on_click=lambda _: page.go("signup"),
            )

            page.views.append(
                View(
                    "login",
                    [
                        AppBar(title=Text("Bank My Wallet"), bgcolor=Colors.BLACK, color='#E8D04A',center_title=True,),
                        Text("Login", size=24, text_align="center"),
                        email_field,
                        password_field,
                        Row([login_button, go_signup_btn], alignment=MainAxisAlignment.CENTER),
                    ],
                )
            )
        global signup_name
        global signup_email
        global signup_phone
        global signup_pass
        global signup_confirm
        global signup_OTP
        global signup_address
        # صفحة إنشاء الحساب
        if page.route == "signup":
            signup_name = TextField(label="Name")
            signup_email = TextField(label="E-mail")
            signup_phone = TextField(label="Phone number")
            signup_pass = TextField(label="Password", password=True, can_reveal_password=True)
            signup_confirm = TextField(label="Confirm password", password=True, can_reveal_password=True)
            signup_OTP = TextField(label="Enter OTP",width=175,max_length=6,keyboard_type=KeyboardType.NUMBER)
            signup_address = TextField(label="Address", width=170)
            options=[
                DropdownOption("Cairo"),
                DropdownOption("Giza"),
                DropdownOption("Alexandria"),
                DropdownOption("Dakahlia"),
                DropdownOption("Red Sea"),
                DropdownOption("Beheira"),
                DropdownOption("Fayoum"),
                DropdownOption("Gharbia"),
                DropdownOption("Ismailia"),
                DropdownOption("Menoufia"),
                DropdownOption("Minya"),
                DropdownOption("Qalyubia"),
                DropdownOption("New Valley"),
                DropdownOption("Suez"),
                DropdownOption("Aswan"),
                DropdownOption("Assiut"),
                DropdownOption("Beni Suef"),
                DropdownOption("Port Said"),
                DropdownOption("Damietta"),
                DropdownOption("Sharkia"),
                DropdownOption("South Sinai"),
                DropdownOption("Kafr El Sheikh"),
                DropdownOption("Matrouh"),
                DropdownOption("Luxor"),
                DropdownOption("Qena"),
                DropdownOption("North Sinai"),
                DropdownOption("Sohag")
            ]
            signup_governorate = Dropdown(
                label="Choose the governorate",
                options=options
            )
            

            # زر إرسال الكود
            def send_otp_click(e):
                def start_cooldown():
                    send_OTP_btn.disabled = True
                    remaining = 40
                    while remaining > 0:
                           send_OTP_btn.text = f"Resend OTP {remaining}s"
                           page.update()
                           time.sleep(1)   
                           remaining -= 1
                    send_OTP_btn.text = "Send OTP"
                    send_OTP_btn.disabled = False
                    page.update()
                threading.Thread(target=start_cooldown, daemon=True).start()
                global otp_code
                otp_code = random.randint(100000, 999999)
                send_email(signup_email.value,
                            f"This is the OTP code {otp_code} so you can activate your account in (Bank My Wallet) and not give it to anyone",
                            "Bank My Wallet"
                )
                
                
                  
                def close_dialog(e):
                    alert1.open = False
                    page.update()
                
                alert1 = AlertDialog(
                    title=("OTP has been sent"),
                    actions=[TextButton("Ok",on_click=close_dialog)],
                    actions_alignment=MainAxisAlignment.END,
                
                )
                
                
                page.overlay.append(alert1)
                alert1.open = True
                page.update()
            
            def go_back(e):
                page.clean() 
                main(page)
                

            global send_OTP_btn
            send_OTP_btn = ElevatedButton(
                "Send OTP",
                width=175,
                style=ButtonStyle(bgcolor="purple", color="white"),
                on_click=send_otp_click,
            )

            signup_button = ElevatedButton(
                "Create account",
                width=170,
                style=ButtonStyle(bgcolor="purple", color="white"),
                on_click=add1
            )
            go_login_btn = ElevatedButton(
                "Login",
                width=170,
                style=ButtonStyle(bgcolor="purple", color="white"),
                on_click=lambda _: page.go("login"),
            )
            
            
            

        
            page.views.append(
                View(
                    "signup",
                    [
                        AppBar(title=Text("Bank My Wallet"), bgcolor=Colors.BLACK, color='#E8D04A',center_title=True,),
                        Text("Create a new account", size=24, text_align="center"),
                        signup_name,
                        signup_email,
                        Row([signup_OTP,send_OTP_btn], alignment=MainAxisAlignment.CENTER),
                        signup_phone,
                        signup_pass,
                        signup_confirm,
                        Row([signup_address, signup_governorate]),
                        
                        
                        
                        
                        Row([signup_button, go_login_btn], alignment=MainAxisAlignment.CENTER),
                        
                    ],
                )
            )
        
        
        
        # الاعدادات 
        if page.route == "setting":
            def toggle_theme(e):
                if page.theme_mode == ThemeMode.LIGHT:
                    page.theme_mode = ThemeMode.DARK
                    btn.text = "Return to light mode ☀️"
                    saver.save("theme", "dark")
                else:
                    page.theme_mode = ThemeMode.LIGHT
                    btn.text = "Night mode🌙"
                    saver.save("theme", "light")
                page.update()
            btn = ElevatedButton(          
                text="Night mode🌙" if page.theme_mode == ThemeMode.LIGHT else "Return to light mode ☀️",
                width=250,
                height=60,
                on_click=toggle_theme
            )
        
            page.views.append(
                View(
                    "setting",
                    [
                       AppBar(title=Text("Settings"), bgcolor=Colors.BLACK, color=Colors.WHITE, center_title=True,),
                       Column([btn], alignment=MainAxisAlignment.CENTER)
                   ]
               )
           )
         #صفحة الرئيسية (1) 
        if page.route == "main1":
            current_email = saver.get("current_user_email")
            card_data = None

            if current_email:
                try:
                    url = "https://bank-my-wallet-default-rtdb.asia-southeast1.firebasedatabase.app/cart_cvv_exp.json"
                    r = requests.get(url)
                    r.raise_for_status()
                    cards = r.json()  # dict من Firebase
                    if cards:
                        for key, val in cards.items():
                            if val.get("email") == current_email:
                                card_data = val
                                break
                except Exception as e:
                    alert = AlertDialog(
                        title=Text("Error fetching card"),
                        content=Text(str(e)),
                        actions=[TextButton("Ok", on_click=lambda e: setattr(alert, "open", False))]
                    )
                    page.overlay.append(alert)
                    alert.open = True
                    page.update()

            # إذا موجود الكارد للمستخدم
            if card_data:
                card1 = Card(
                    elevation=8,
                    content=Container(
                        width=360,
                        height=210,
                        border_radius=20,
                        padding=0,
                        gradient=LinearGradient(
                            begin=alignment.top_left,
                            end=alignment.bottom_right,
                            colors=[Colors.BLUE_600, Colors.BLUE_900],
                        ),
                        content=Stack(
                            controls=[
                                Text("My Wallet Card", size=16, weight="bold", color=Colors.WHITE, top=15, left=20),
                                Text(card_data["cart"], size=26, weight="bold", color=Colors.WHITE, top=85, left=20),
                                Text(f"EXP: {card_data['exp']}", size=14, weight="bold", color=Colors.WHITE, bottom=20, right=20),
                                Text(f"CVV: {card_data['cvv']}", size=14, weight="bold", color=Colors.WHITE, bottom=20, left=20)
                            ]
                        )
                    )
                )
            else:
                # إذا لا يوجد كارد للمستخدم، يظهر فارغ أو نص توضيحي
                card1 = Card(
                    elevation=8,
                    content=Container(
                        width=360,
                        height=210,
                        border_radius=20,
                        padding=0,
                        gradient=LinearGradient(
                            begin=alignment.top_left,
                            end=alignment.bottom_right,
                            colors=[Colors.BLUE_300, Colors.BLUE_600],
                        ),
                        content=Text("No card found. Go create one in 'Visa'", color=Colors.WHITE, size=20, text_align="center")
                    )
                )

            mou = Row([card1], alignment=MainAxisAlignment.CENTER)
            page.views.append(
                View(
                    "main1",
                    [
                        AppBar(title=Text("Bank My Wallet"), center_title=True, bgcolor=Colors.BLACK, color=Colors.WHITE),
                        mou
                    ]
                )
            )
            page.update()
   # حساب تعريفي 
        if page.route == "profile":
            current_email = saver.get("current_user_email")  # الإيميل اللي سجل الدخول
            if not current_email:
                page.go("/")  # لو مفيش مستخدم مسجل دخول ارجع للرئيسية
            else:
                try:
                    r = requests.get("https://bank-my-wallet-default-rtdb.asia-southeast1.firebasedatabase.app/bank_my_wallet.json")
                    r.raise_for_status()  # لو حصل خطأ يرمي استثناء
                    users = r.json()  # البيانات كلها
                except Exception as e:
                    alert = AlertDialog(
                        title=Text("Firebase connection error"),
                        content=Text(str(e)),
                        actions=[TextButton("Ok", on_click=lambda e: setattr(alert, "open", False))],
                    )
                    page.overlay.append(alert)
                    alert.open = True
                    page.update()
                    users = None

                user_data = None
                if users and isinstance(users, dict):
                    for uid, data in users.items():
                        if not isinstance(data, dict):
                            continue
                        if data.get("email") == current_email:
                            user_data = data
                            break

                if not user_data:
                    alert = AlertDialog(
                        title=Text("User not found"),
                        actions=[TextButton("Ok", on_click=lambda e: page.go("/"))],
                    )
                    page.overlay.append(alert)
                    alert.open = True
                    page.update()
                else:
                    # عرض بيانات المستخدم الحالي
                    card_view = Card(
                        elevation=8,
                        content=Container(
                            width=360,
                            height=220,
                            border_radius=20,
                            padding=20,
                            gradient=LinearGradient(
                                begin=alignment.top_left,
                                end=alignment.bottom_right,
                                colors=[Colors.BLUE, Colors.BLUE],
                            ),
                            content=Column(
                                [
                                    Text(f"Name: {user_data.get('name','')}", size=18, weight="bold", color=Colors.WHITE),
                                    Text(f"Email: {user_data.get('email','')}", size=16, color=Colors.WHITE),
                                    Text(f"Phone: {user_data.get('phone','')}", size=16, color=Colors.WHITE),
                                    Text(f"Address: {user_data.get('address','')}", size=16, color=Colors.WHITE),
                                ],
                                alignment=MainAxisAlignment.START,
                            )
                        )
                    )

                    # زر تسجيل الخروج
                    def sign_out(e):
                        saver.save("current_user_email", None)
                        page.go("/")

                    logout_btn = Row([ElevatedButton("Sign Out", bgcolor=Colors.RED, on_click=sign_out, width=200)], alignment=MainAxisAlignment.CENTER)

                    # إضافة العرض للبروفايل
                    page.views.append(
                        View(
                            "profile",
                            [
                                AppBar(
                                    title=Text("Profile"),
                                    center_title=True,
                                    bgcolor=Colors.BLACK,
                                    color=Colors.WHITE,
                                    leading=IconButton(Icons.ARROW_BACK, on_click=lambda _: page.go("main1"))
                                ),
                                Column([card_view, logout_btn], alignment=MainAxisAlignment.CENTER, spacing=20)
                            ]
                        )
                    )
            page.update()




        # الدعم 
        if page.route == "support":
            def copy_number(e):
                page.set_clipboard(number)

                def close_dialog(ev):
                    alert1.open = False
                    page.update()

                alert1 = AlertDialog(
                    title=Text("Copied"),
                    actions=[TextButton("Ok", on_click=close_dialog)],
                    actions_alignment=MainAxisAlignment.END,
                )
                page.overlay.append(alert1)
                alert1.open = True
                page.update()

            copy_button = IconButton(
                icon=Icons.CONTENT_COPY,
                icon_color=Colors.WHITE,
                on_click=copy_number,
                
            
                
            )       
            number = "+201006861708"
            def open_whatsapp(e):
                webbrowser.open("""
                                https://wa.me/201006861708?text=%D9%85%D8%B1%D8%AD%D8%A8%D9%8B%D8%A7%D8%8C%20%D8%A3%D8%B1%D9%8A%D8%AF%20%D8%A7%D9%84%D8%AA%D9%88%D8%A7%D8%B5%D9%84%20%D9%85%D8%B9%D9%83%D9%85%20%D8%A8%D8%AE%D8%B5%D9%88%D8%B5%20%D8%A7%D9%84%D8%AF%D8%B9%D9%85%20%D8%A3%D9%88%20%D8%A7%D8%B3%D8%AA%D9%81%D8%B3%D8%A7%D8%B1%20%D8%AD%D9%88%D9%84%20%D8%AE%D8%AF%D9%85%D8%A7%D8%AA%D9%83%D9%85
                                """)

            image1 = Row([
                Image(src="qr_code.png",width=200)
            ],alignment=MainAxisAlignment.CENTER)
            
            link1 = Row([
                ElevatedButton(
                    "Contact us on WhatsApp",
                    bgcolor=Colors.GREEN,
                    color=Colors.WHITE,
                    on_click=open_whatsapp
                )
            ],alignment=MainAxisAlignment.CENTER)
            txt1 = Text("____________________________________________________________________________________________________________________")
            txt2 = Text("To contact customer service, call this number",size=16)
            
            card3 = Card(
                content=Container(
                    padding=20,
                    bgcolor=Colors.BLUE_300,
                    border_radius=10,
                    content=Row(
                        [
                            Text(number, size=24, weight="bold", color=Colors.WHITE),
                            copy_button
                        ],
                        alignment=MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=CrossAxisAlignment.CENTER
                    )
                )
            )             
            
            page.views.append(
                View(
                    "support",
                    [
                       AppBar(title=Text("support"),
                              center_title=True,
                              bgcolor=Colors.BLACK,
                              color=Colors.WHITE,
                              leading=IconButton(Icons.ARROW_BACK,on_click=lambda _: page.go("main1")),
                              ),
                       image1,
                       link1,
                       txt1,
                       txt2,
                       card3,
                   ]
               )
           )
            
        if page.route == "who_are_we":
            
            roww = Row([
                Text ("Who are we?", size=38, font_family="Gabriola")
            ],alignment=MainAxisAlignment.CENTER)
            
            roww2 = Row([
                Text(" Bank My Wallet الرقمي",size=18)
            ],alignment=MainAxisAlignment.CENTER, rtl=True)
            
            def open_website(o):
                webbrowser.open("https://rofy-m.gt.tc")
            tbtn = Row([
                TextButton("للمزيد اضغط هنا",on_click=open_website)
            ],alignment=MainAxisAlignment.CENTER, rtl=True)
            roww1 = Row([
                Text("""
تحكم بأموالك بسهولة وأمان مع Bank My Wallet الرقمي.
تابع رصيدك، حول أموالك، وادفع في أي وقت ومن أي مكان.

نقدم لك خيارات متعددة للدفع :
Visa Card،
MasterCard،
Meeza Card،
American Express
لتجربة مالية سلسة وآمنة.

مع Bank My Wallet الرقمي،
أموالك بين يديك، بسيط، آمن، وسهل الاستخدام.
                     """, rtl=True)
            ])
            
            
            
            page.views.append(
                View(
                    "who_are_we",
                    [
                       AppBar(title=Text("Who are we"),
                              center_title=True,
                              bgcolor=Colors.BLACK,
                              color=Colors.WHITE,
                              leading=IconButton(Icons.ARROW_BACK,on_click=lambda _: page.go("main1")),
                              ),
                       roww,
                       roww2,
                       roww1,
                       tbtn
                   ]
               )
           )
            
        #2 الاعدادات 
        if page.route == "settings":
            def toggle_theme(e):
                if page.theme_mode == ThemeMode.LIGHT:
                    page.theme_mode = ThemeMode.DARK
                    btn.text = "Return to light mode ☀️"
                    saver.save("theme", "dark")
                else:
                    page.theme_mode = ThemeMode.LIGHT
                    btn.text = "Night mode🌙"
                    saver.save("theme", "light")
                page.update()
            btn = ElevatedButton(          
                text="Night mode🌙" if page.theme_mode == ThemeMode.LIGHT else "Return to light mode ☀️",
                width=250,
                height=60,
                on_click=toggle_theme
            )
        
            page.views.append(
                View(
                    "settings",
                    [
                       AppBar(title=Text("Settings"),
                              center_title=True,
                              bgcolor=Colors.BLACK, color=Colors.WHITE,
                              leading=IconButton(Icons.ARROW_BACK,on_click=lambda _: page.go("main1"))),
                       Column([btn], alignment=MainAxisAlignment.CENTER)
                   ]
               )
           )
        
        # صفحة انشاء الفيزا 
        if page.route == "visa":
            global tf1, tf2, tf3
            txt3 = Text(
                "The card that came out of the bot and put it here",
                text_align="center",
                size=15.5,
                color='#E8D04A'
            )

            # الحقول
            tf1 = TextField(
                label="Card Number",
                keyboard_type=KeyboardType.NUMBER,
                hint_text="xxxx xxxx xxxx xxxx",
                max_length=19
            )
            tf2 = TextField(
                label="CVV",
                width=165,
                keyboard_type=KeyboardType.NUMBER,
                hint_text="xxx",
                max_length=3
            )
            tf3 = TextField(
                label="EXP",
                width=165,
                keyboard_type=KeyboardType.NUMBER,
                hint_text="MM/YY",
                max_length=5
            )

            def alert_dialog(message):
                def close_alert(e):
                    alert.open = False
                    page.update()
                alert = AlertDialog(
                    title=Text(message),
                    actions=[TextButton("Ok", on_click=close_alert)],
                    actions_alignment=MainAxisAlignment.END
                )
                page.overlay.append(alert)
                alert.open = True
                page.update()

            # فورمات الكارد
            def card_change(e):
                val = tf1.value.replace(" ", "")
                if val != "" and not val.isdigit():
                    alert_dialog("Only numbers allowed in Card Number")
                    tf1.value = ""
                    page.update()
                    return
                tf1.value = " ".join([val[i:i+4] for i in range(0, len(val), 4)])
                page.update()

            def cvv_change(e):
                val = tf2.value
                if val != "" and not val.isdigit():
                    alert_dialog("Only numbers allowed in CVV")
                    tf2.value = ""
                    page.update()

            def exp_change(e):
                val = tf3.value.replace("/", "")
                if val != "" and not val.isdigit():
                    alert_dialog("Only numbers allowed in Exp Date")
                    tf3.value = ""
                    page.update()
                    return
                if len(val) > 2:
                    val = val[:2] + "/" + val[2:4]
                tf3.value = val
                page.update()

            tf1.on_change = card_change
            tf2.on_change = cvv_change
            tf3.on_change = exp_change

            # حفظ الكارد باستخدام requests
            def save12(e):
                if len(tf1.value.replace(" ", "")) < 16:
                    alert_dialog("Enter the correct card number, it must be 16 digits")
                    return
                if len(tf2.value) < 3:
                    alert_dialog("Enter the correct CVV number, it must be 3 digits")
                    return
                if len(tf3.value) < 5 or "/" not in tf3.value:
                    alert_dialog("Enter the correct EXP number in MM/YY format")
                    return

                try:
                    data = {
                        "cart": tf1.value,
                        "cvv": tf2.value,
                        "exp": tf3.value
                    }
                    url = "https://bank-my-wallet-default-rtdb.asia-southeast1.firebasedatabase.app/cart_cvv_exp.json"
                    r = requests.post(url, json=data)
                    r.raise_for_status()
                    page.go("main1")
                    page.update()
                except Exception as ex:
                    alert_dialog(f"Error saving card: {ex}")

            # الأزرار
            bn1 = Row([ElevatedButton("Create Card", width=150, height=50, on_click=save12)], alignment=MainAxisAlignment.CENTER)
            bn2 = Row([ElevatedButton("Enter the bot to get the card", width=250, bgcolor='#E8D04A', color="white",
                                    on_click=lambda e: webbrowser.open("https://t.me/bank_my_wallet_bot"))], alignment=MainAxisAlignment.CENTER)
            bn3 = Row([ElevatedButton("Return to the login page", width=250, bgcolor='#E8D04A', color="white",
                                    on_click=lambda e: page.go("/"))], alignment=MainAxisAlignment.CENTER)

            page.views.append(
                View(
                    "visa",
                    [
                        AppBar(
                            title=Text("Create Card"),
                            center_title=True,
                            bgcolor=Colors.BLACK,
                            color=Colors.WHITE,
                            leading=Text("")
                        ),
                        txt3,
                        tf1,
                        Row([tf2, tf3], alignment=MainAxisAlignment.START, spacing=20),
                        bn1,
                        bn2,
                        bn3
                    ]
                )
            )
        page.update()


    def page_go(view):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = page_go
    page.go(page.route)

app(main)
