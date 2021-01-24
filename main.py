import mysql.connector
from datetime import date
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
import pandas as pd
from kivy.core.window import Window
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDToolbar, MDBottomAppBar
from kivy.clock import Clock
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.base import EventLoop
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.gridlayout import GridLayout
from kivymd.uix.label import MDLabel


Window.size = (360, 600)
Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_expo'}
Window.softinput_mode = 'below_target'

db = mysql.connector.connect(host="bpjum1fu8uithbn7fk2n-mysql.services.clever-cloud.com", user="utt8pcxyfysh9vwz",
                             passwd="fFYduFGCjwhnyLrc1hIy", database="bpjum1fu8uithbn7fk2n")

username_current = ""
result = []
orderNum_current = None


class ScreenManagement(ScreenManager):
    pass


class AnimCard(MagicBehavior, MDCard):
    pass


class LogInScreen(Screen):
    def getUsername(self):
        global username_current
        username_current = self.ids.username.text

    def logIn_verify(self):
        global result
        if (self.ids.username.text, self.ids.password.text) in result:
            self.ids.password.text = ""
            return 1

        else:
            self.ids.animCard_logIn.shake()
            Snackbar(text='Verify your credentials').show()
            return 0


class ActivityScreen(Screen):
    pass


class dialogBox(BoxLayout):
    pass


class TopToolbar(MDToolbar):

    dialog = None

    def logOut(self):
        MDApp.get_running_app().root.current = 'logIn'

    def getOrderNum(self):
        self.dialog = MDDialog(
            title="Enter the order code: ",
            type = 'custom',
            content_cls = dialogBox(),
            buttons=[
                MDFlatButton(text="Close", on_release=self.dialogDismiss),
                MDFlatButton(text="Proceed", on_release = self.verifyOrder)
            ],
            size_hint_x=0.75
        )
        self.dialog.open()

    def dialogDismiss(self, dialogRef):
        self.dialog.dismiss()

    def verifyOrder(self, dialogRef):
        global orderNum_current
        orderNum_current = self.dialog.content_cls.ids.orderNum.text
        # print(orderNum_current)
        self.dialog.dismiss()
        MDApp.get_running_app().root.current = "bill"


class BillScreen(Screen):
    global orderNum_current, username_current

    orderDetails = None
    
    def on_enter(self):
        # print("In Bill Screen", orderNum_current, username_current)

        orderNum = str(orderNum_current) + str(date.today().year) + str(date.today().month) + str(date.today().day)
        db.cmd_reset_connection()
        # print(orderNum)

        fetchOrder_statement = "select dish.dishID, orderDishTable.dish, orderDishTable.quantity, dish.price from orderDishTable left join dish on dish.dish = orderDishTable.dish where dish.username = %s and orderDishTable.ordernum in (select ordernum from orderDetailsTimeTable where orderStatus = 1 and ordernum = %s);"
        cursor = db.cursor()
        cursor.execute(fetchOrder_statement, (username_current,orderNum))
        self.orderDetails = pd.DataFrame(cursor.fetchall()).rename(columns={0:'DishID', 1:'Dish', 2: 'Quantity', 3: 'Price'}).reset_index(drop=True)
        cursor.close()

        if self.orderDetails.empty:
            Snackbar(text = "Invalid code. Kindly recheck.").show()
            MDApp.get_running_app().root.current = "view_dish"

        else:
            self.ids.bill_values.clear_widgets()
            totalPay = 0
            for i in range(len(self.orderDetails)):
                self.orderDetailsItem = GridLayout(cols = 5)
                self.orderDetailsItem.add_widget(MDLabel(text = str(self.orderDetails.loc[i, 'DishID'])))
                self.orderDetailsItem.add_widget(MDLabel(text = self.orderDetails.loc[i, 'Dish']))
                self.orderDetailsItem.add_widget(MDLabel(text= str(self.orderDetails.loc[i, 'Quantity'])))
                self.orderDetailsItem.add_widget(MDLabel(text="\u20B9" + str(self.orderDetails.loc[i, 'Price'])))
                self.orderDetailsItem.add_widget(MDLabel(text="\u20B9" + str(self.orderDetails.loc[i, 'Quantity'] * self.orderDetails.loc[i, 'Price'])))
                self.ids.bill_values.add_widget(self.orderDetailsItem)
                totalPay += self.orderDetails.loc[i, 'Quantity'] * self.orderDetails.loc[i, 'Price']
                self.ids.bill_totalPay.text = "Total:    \u20B9" + str(totalPay)

    def printBill(self):
        global username_current, orderNum_current
        # print(str(orderNum_current) + str(date.today().year) + str(date.today().month) + str(date.today().day))
        cursor = db.cursor()
        # print(self.orderDetails)
        for i in range(len(self.orderDetails)):
            alterOutstanding_statement = "update dish set orderOutStanding = orderOutStanding - %s where dish = %s and username = %s"
            alterOutstanding_details = (str(self.orderDetails.loc[i, "Quantity"]), self.orderDetails.loc[i, "Dish"], username_current)
            # print(alterOutstanding_details)
            cursor.execute(alterOutstanding_statement, alterOutstanding_details)
        cursor.execute("update orderDetailsTimeTable set orderStatus = 0 where ordernum = %s", (str(orderNum_current) + str(date.today().year) + str(date.today().month) + str(date.today().day),))
        db.commit()
        Snackbar(text="Order completed").show()
        MDApp.get_running_app().root.current = "view_dish"


class FunctionsBar(MDBottomAppBar):
    def goToAdd(self):
        if MDApp.get_running_app().root.current != 'add_dish':
            MDApp.get_running_app().root.current = 'add_dish'

    def goToModify(self):
        if MDApp.get_running_app().root.current != 'modify_dish':
            MDApp.get_running_app().root.current = 'modify_dish'

    def goToView(self):
        if MDApp.get_running_app().root.current != 'view_dish':
            MDApp.get_running_app().root.current = 'view_dish'

class Dish_AddScreen(Screen):
    global username_current

    def dishAdd_cafe(self):

        cursor = db.cursor()
        try:
            insertDish = "insert into dish(username, dish, price, available) values (%s, %s, %s, %s)"
            i = (username_current, self.ids.dishName_entry.text.title(), int(self.ids.price_entry.text), "1")

            cursor = db.cursor()
            cursor.execute(insertDish, i)
            db.commit()
            Snackbar(text='Added successfully').show()

        except:
            self.ids.animCard_add.shake()
            Snackbar(text='Already added or not in proper format').show()


class Dish_ModifyScreen(Screen):

    def on_enter(self):
        db.cmd_reset_connection()
        self.cursor = db.cursor()
        self.search = "select * from dish where username = \'" + username_current + "\'"
        self.cursor.execute(self.search)
        self.data = pd.DataFrame(self.cursor.fetchall())
        self.ids.dishNames_spinner.values = self.data[1].tolist()
        self.cursor.close()

    def details_filler(self, text):
        self.text = text
        dish_status = self.data[self.data[1] == text].values.tolist()[0]
        self.ids.dishPrice_modify.text = str(dish_status[2])
        self.ids.availability_switch.active = True if dish_status[3] == 1 else False

    def dishModify_cafe(self):
        try:
            self.cursor = db.cursor()
            self.availablity_status_toModify = 1 if self.ids.availability_switch.active == True else 0
            modify = "update dish set price = %s, available = %s where (username, dish) = (%s, %s)"
            modify_details = (int(self.ids.dishPrice_modify.text), self.availablity_status_toModify, username_current, self.text)
            self.cursor.execute(modify, modify_details)
            db.commit()
            self.cursor.close()
            Snackbar(text='Modified successfully').show()

        except ValueError:
            self.ids.animCard_modify.shake()
            Snackbar(text='Invalid. Check again').show()


class Dish_ViewScreen(Screen):

    def on_pre_enter(self):
        global username_current
        db.cmd_reset_connection()

        cursor = db.cursor()
        cursor.execute("update orderDetailsTimeTable set orderStatus = -1 where timeTakeAway < date_sub(now(), interval 30 minute) and hotelName = %s", (username_current,))
        db.commit()

        try:
            # print(username_current)
            # print(destroyOldOrders)
            search = "select dish, orderOutstanding from dish where username = %s and orderOutstanding > 0"
            cursor.execute(search, (username_current,))

            self.viewData = pd.DataFrame(cursor.fetchall()).rename(columns={0: "Dish", 1: "Orders to be delivered"}).sort_values(by="Orders to be delivered",ascending=False).reset_index(drop=True)
            cursor.close()

            self.ids.container.clear_widgets()


            for i in range(len(self.viewData)):
                viewDishData = TwoLineListItem(
                    text = self.viewData.loc[i][0],
                    secondary_text = str(self.viewData.loc[i][1]),
                    bg_color = (153/255,153/255,153/255,1)
                )
                self.ids.container.add_widget(viewDishData)
        except KeyError:
            pass


    def refreshScreen(self):
        def refresh(interval):
            db.cmd_reset_connection()
            self.on_pre_enter()
            self.ids.refresh_layout.refresh_done()

        Clock.schedule_once(refresh,1)

    # def negate(self, instance):
    #
    #     dishName = " ".join(instance.text.split()[:-1])
    #     try:
    #         negateDelivered = "update dish set orderOutstanding = orderOutstanding - 1 where (username, dish) = (\'" + username_current + "\', \'" + \
    #                           dishName + "\')"
    #         self.cursor.execute(negateDelivered)
    #         instance.text = dishName + "\n" + str(int(instance.text.split()[-1]) - 1)
    #         self.viewData.loc[(self.viewData['Dish'] == dishName), "Orders to be delivered"] -= 1
    #         db.commit()
    #
    #     except:
    #         self.ids.animCard_view.shake()
    #         Snackbar(text='Orders satisfied').show()


screenManager = ScreenManager()
screenManager.add_widget(LogInScreen(name='logIn'))
screenManager.add_widget(ActivityScreen(name='activity'))
screenManager.add_widget(Dish_AddScreen(name='add_dish'))
screenManager.add_widget(Dish_ModifyScreen(name='modify_dish'))
screenManager.add_widget(Dish_ViewScreen(name='view_dish'))


class cafeApp(MDApp):
    def build(self):
        global result
        # print(MDApp.get_running_app().root.ids)
        self.theme_cls.primary_palette = 'BlueGray'
        # self.theme_cls.primary_hue = '500'
        local_cursor = db.cursor()
        local_cursor.execute("select * from login")
        result = local_cursor.fetchall()
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            if MDApp.get_running_app().root.current == 'activity':
                MDApp.get_running_app().root.current = 'logIn'
            elif MDApp.get_running_app().root.current == 'logIn':
                MDApp.get_running_app().stop()
            else:
                MDApp.get_running_app().root.current = 'view_dish'
            return True


if __name__ == "__main__":
    cafeApp().run()
