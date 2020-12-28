import mysql.connector
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
import pandas as pd
from kivy.uix.button import Button
from kivy.core.window import Window
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDToolbar, MDBottomAppBar
from kivymd.uix.gridlayout import GridLayout

# Window.size = (360, 600)
Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_expo'}
Window.softinput_mode = 'below_target'

db = mysql.connector.connect(host="bpjum1fu8uithbn7fk2n-mysql.services.clever-cloud.com", user="utt8pcxyfysh9vwz",
                             passwd="fFYduFGCjwhnyLrc1hIy", database="bpjum1fu8uithbn7fk2n")

username_current = ""
result = []


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

    def dialog_close(self, obj):
        self.dialog.dismiss()


class ActivityScreen(Screen):
    pass


class TopToolbar(MDToolbar):
    def logOut(self):
        MDApp.get_running_app().root.current = 'logIn'


class FunctionsBar(MDBottomAppBar):
    def goToAdd(self):
        MDApp.get_running_app().root.current = 'activity'
        MDApp.get_running_app().root.current = 'add_dish'

    def goToModify(self):
        MDApp.get_running_app().root.current = 'activity'
        MDApp.get_running_app().root.current = 'modify_dish'

    def goToView(self):
        MDApp.get_running_app().root.current = 'activity'
        MDApp.get_running_app().root.current = 'view_dish'


class Dish_AddScreen(Screen):
    global username_current, db

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
        try:
            self.availablity_status_toModify = 1 if self.ids.availability_switch.active == True else 0
            modify = "update dish set price = %s, available = %s where (username, dish) = (%s, %s)"
            modify_details = (int(self.ids.dishPrice_modify.text), self.availablity_status_toModify, username_current, self.text)
            self.cursor.execute(modify, modify_details)
            db.commit()
            Snackbar(text='Modified successfully').show()

        except ValueError:
            self.ids.animCard_modify.shake()
            Snackbar(text='Invalid. Check again').show()


class Dish_ViewScreen(Screen):
    def on_pre_enter(self):
        self.cursor = db.cursor()
        search = "select dish, order_Outstanding from dish where username = \'" + username_current + "\' and order_Outstanding > 0"
        self.cursor.execute(search)

        self.viewData = pd.DataFrame(self.cursor.fetchall()).rename(columns={0: "Dish", 1: "Orders to be delivered"}).sort_values(by="Orders to be delivered",ascending=False).reset_index(drop=True)

        self.ids.container.clear_widgets()

        k = 0
        for i in range(0, len(self.viewData), 10):
            layout = GridLayout(cols=2, spacing=10, padding=10)
            for j in range(i, i + 10):
                if j == len(self.viewData):
                    break
                text = self.viewData.loc[k][0] + "\n" + str(self.viewData.loc[k][1])
                items = Button(text=text, size_hint_y=None, height=45, halign='center', on_release=self.negate)
                layout.add_widget(items)
                k += 1
            self.ids.container.add_widget(layout)

    def negate(self, instance):
        dishName = " ".join(instance.text.split()[:-1])
        try:
            negateDelivered = "update dish set order_OutStanding = order_OutStanding - 1 where (username, dish) = (\'" + username_current + "\', \'" + \
                              dishName + "\')"
            self.cursor.execute(negateDelivered)
            instance.text = dishName + "\n" + str(int(instance.text.split()[-1]) - 1)
            self.viewData.loc[(self.viewData['Dish'] == dishName), "Orders to be delivered"] -= 1
            db.commit()

        except:
            self.ids.animCard_view.shake()
            Snackbar(text='Orders satisfied').show()


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
