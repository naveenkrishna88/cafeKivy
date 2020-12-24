import mysql.connector
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.floatlayout import MDFloatLayout
import pandas as pd
from kivy.uix.button import Button

db = mysql.connector.connect(host="bpjum1fu8uithbn7fk2n-mysql.services.clever-cloud.com", user="utt8pcxyfysh9vwz",
                             passwd="fFYduFGCjwhnyLrc1hIy", database="bpjum1fu8uithbn7fk2n")

username_current = ""
result = []


class ScreenManagement(ScreenManager):
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
            self.ids.confirmation_logIn.text = "Wrong entry"
            return 0

    def dialog_close(self, obj):
        self.dialog.dismiss()


class ActivityScreen(Screen):
    pass


class FunctionsBar(MDFloatLayout):
    pass


class Dish_AddScreen(Screen):
    global username_current, db

    def dishAdd_cafe(self):

        cursor = db.cursor()

        try:
            self.ids.confirmation_add.text = ""
            insertDish = "insert into dish(username, dish, price, available) values (%s, %s, %s, %s)"
            i = (username_current, self.ids.dishName_entry.text.title(), int(self.ids.price_entry.text), "1")

            cursor = db.cursor()
            cursor.execute(insertDish, i)
            db.commit()
            self.ids.confirmation_add.text = "Added Successfully!"

        except:
            self.ids.confirmation_add.text = "Check the desc"


class Dish_ModifyScreen(Screen):

    def on_enter(self):
        self.cursor = db.cursor()
        self.search = "select * from dish where username = \'" + username_current + "\'"
        self.cursor.execute(self.search)
        self.data = pd.DataFrame(self.cursor.fetchall())
        self.ids.dishNames_spinner.values = self.data[1].tolist()

    def details_filler(self, text):
        self.text = text
        dish_status = self.data[self.data[1] == text].values.tolist()[0]
        self.ids.dishPrice_modify.text = str(dish_status[2])
        self.ids.availability_switch.active = True if dish_status[3] == 1 else False

    def dishModify_cafe(self):
        self.ids.confirmation_modify.text = ""
        try:
            self.availablity_status_toModify = 1 if self.ids.availability_switch.active == True else 0
            modify = "update dish set price = %s, available = %s where (username, dish) = (%s, %s)"
            modify_details = (
                int(self.ids.dishPrice_modify.text), self.availablity_status_toModify, username_current, self.text)
            self.cursor.execute(modify, modify_details)
            db.commit()
            self.ids.confirmation_modify.text = "Modified Successfully!"

        except ValueError:
            self.ids.confirmation_modify.text = "Error in modifying!"


class Dish_ViewScreen(Screen):
    def on_pre_enter(self):
        self.cursor = db.cursor()
        search = "select dish, order_OutStanding from dish where username = \'" + username_current + "\'"
        self.cursor.execute(search)

        self.viewData = pd.DataFrame(self.cursor.fetchall()).rename(
            columns={0: "Dish", 1: "Orders to be delivered"}).sort_values(by="Orders to be delivered",ascending=False).reset_index(drop=True)

        self.ids.container.clear_widgets()
        for i in range(len(self.viewData)):
            if self.viewData.loc[i][1] == 0:
                break
            else:
                text = self.viewData.loc[i][0] + "\n" + str(self.viewData.loc[i][1])
                items = Button(text=text, size_hint=(None, None), size=(125, 50), halign='center',
                               on_release=self.negate)
                self.ids.container.add_widget(items)

    def negate(self, instance):
        dishName = " ".join(instance.text.split()[:-1])
        try:
            self.clear_confirmation()
            negateDelivered = "update dish set order_OutStanding = order_OutStanding - 1 where (username, dish) = (\'" + username_current + "\', \'" + \
                              dishName + "\')"
            self.cursor.execute(negateDelivered)
            instance.text = dishName + "\n" + str(int(instance.text.split()[-1]) - 1)
            self.viewData.loc[(self.viewData['Dish'] == dishName), "Orders to be delivered"] -= 1
            db.commit()

        except:
            self.ids.confirmation_view.text = "Orders satisfied!"

    def clear_confirmation(self):
        self.ids.confirmation_view.text = ""


screenManager = ScreenManager()
screenManager.add_widget(LogInScreen(name='logIn'))
screenManager.add_widget(ActivityScreen(name='activity'))
screenManager.add_widget(Dish_AddScreen(name='add_dish'))
screenManager.add_widget(Dish_ModifyScreen(name='modify_dish'))
screenManager.add_widget(Dish_ViewScreen(name='view_dish'))


class cafeApp(MDApp):
    def build(self):
        global result
        self.theme_cls.primary_palette = 'BlueGray'
        # self.theme_cls.primary_hue = '500'
        local_cursor = db.cursor()
        local_cursor.execute("select * from login")
        result = local_cursor.fetchall()


if __name__ == "__main__":
    cafeApp().run()