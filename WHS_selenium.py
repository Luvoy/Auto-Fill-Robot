# -*- coding: utf-8 -*-
# @author rc431@cummins.com
# @Time 2020/3/2
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
import datetime
import time


class AutoWHS():
    def __init__(self, username_str, password_str, explorer_type,
                 driver_path_str):
        self.explorer_type = explorer_type
        if self.explorer_type.lower() == "chrome":
            self.wb = webdriver.Chrome(driver_path_str)
        elif self.explorer_type.lower() == 'ie':
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            DesiredCapabilities.INTERNETEXPLORER[
                'ignoreProtectedModeSettings'] = True
            # ie记得关闭保护模式
            self.wb = webdriver.Ie(driver_path_str)
        elif self.explorer_type.lower() == "firefox":
            self.wb = webdriver.Firefox(executable_path=driver_path_str)
        else:
            exit("Explorer type is not supported!")
        self.username = username_str
        self.password = password_str
        self.right_date_index_list = []

    def login(self):
        self.wb.maximize_window()
        self.wb.get("http://whm.bfcec.com/login")
        self.wb.find_element_by_xpath("//input[@id='userName']").send_keys(
            self.username)
        self.wb.find_element_by_xpath("//input[@id='password']").send_keys(
            self.password)
        time.sleep(1)
        self.wb.find_element_by_xpath(
            "//button[@class='btn green pull-right']").click()
        time.sleep(1)
        self.wb.get("http://whm.bfcec.com/time/register")

    def close_dialog(self):
        try:
            box = self.wb.find_element_by_xpath(
                "//div[@class='layui-layer-title']")
        except NoSuchElementException:
            print("no such element")
        else:
            self.wb.find_element_by_xpath(
                "//a[@class='layui-layer-btn0']").click()
        finally:
            time.sleep(0.5)

    @staticmethod
    def now_in_2months(data_start_str, date_end_str):

        start_date = datetime.datetime.strptime(data_start_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(date_end_str, "%Y-%m-%d")
        now_date = time.localtime(time.time())

        # start_date_tuple=(start_date.year,start_date.month,start_date.day)
        # end_date_tuple=(end_date.year,end_date.month,end_date.day)
        # now_date_tuple = (now_date.tm_year, now_date.tm_mon,now_date.tm_mday)

        start_date_tuple = (start_date.year, start_date.month)
        end_date_tuple = (end_date.year, end_date.month)
        now_date_tuple = (now_date.tm_year, now_date.tm_mon)

        # print(start_date_tuple,end_date_tuple,now_date_tuple)
        if start_date_tuple <= now_date_tuple and now_date_tuple <= end_date_tuple:
            return True
        else:
            return False

    def get_right_dates(self):
        date_selector = Select(
            self.wb.find_element_by_xpath("//select[@id='selectedDate']"))
        select_all_list = date_selector.options
        for i in select_all_list:
            if self.now_in_2months(i.get_attribute("valstart"),
                                   i.get_attribute("valend")):
                self.right_date_index_list.append(i.get_property("index"))

    def parse_date_list(self):
        for i in self.right_date_index_list:
            # 每一遍都要刷新selector
            date_selector = Select(
                self.wb.find_element_by_xpath("//select[@id='selectedDate']"))
            date_selector.select_by_index(str(i))
            self.close_dialog()
            time.sleep(0.5)
            check_result_info = self.wb.find_element_by_xpath(
                "//span[@id='checkResultInfo']").text
            if check_result_info == "已经提交审核":
                print("下拉日期选择 " + str(i) + ": 已经提交审核")
                time.sleep(0.5)
            else:
                print("下拉日期选择 " + str(i) + ": 正在填充表单")
                self.fill_time_table()
                time.sleep(0.5)

    def fill_time_table(self):
        time_table_rows = self.wb.find_elements_by_xpath(
            "//tr[starts-with(@id,'fillTimeRow')]")
        proj_list = []

        if len(time_table_rows) == 0:
            print("这一表单没有行，正在添加")
            self.wb.find_element_by_xpath(
                "//button[@id='addFileTimeRow']").click()
            time_table_rows = self.wb.find_elements_by_xpath(
                "//tr[starts-with(@id,'fillTimeRow')]")

        proj_list = time_table_rows[0].find_elements_by_xpath(
            ".//option[@attrsn]")

        ptr = 0
        while True:
            proj_selector = Select(
                time_table_rows[ptr].find_elements_by_xpath(".//select")[0])
            task_selector = Select(
                time_table_rows[ptr].find_elements_by_xpath(".//select")[1])
            proj_selector.select_by_index(str(1 + ptr))
            time.sleep(0.5)
            task_selector.select_by_index(len(task_selector.options) - 1)
            time.sleep(0.5)
            for i in time_table_rows[ptr].find_elements_by_xpath(".//input"):
                d = i.get_attribute("name")
                if "day6" in d or "day7" in d:
                    pass
                else:
                    i.send_keys("4")
                    time.sleep(0.6)
            ptr += 1
            if ptr < len(proj_list):
                self.wb.find_element_by_xpath(
                    "//button[@id='addFileTimeRow']").click()
                time_table_rows = self.wb.find_elements_by_xpath(
                    "//tr[starts-with(@id,'fillTimeRow')]")
            else:
                break
        time.sleep(0.5)
        if self.wb.find_element_by_xpath("//td[@id='all_sum']").text == '40':
            self.wb.find_element_by_xpath(
                "//button[@id='btnSubmitButton']").click()
            time.sleep(3)
            dig_alert = self.wb.switch_to.alert
            time.sleep(0.3)
            dig_alert.accept()  # 接受弹窗
            time.sleep(0.5)
        else:
            print("Error, 某个工时表单填充失败！")

    def logout(self):
        self.wb.get("http://whm.bfcec.com/logout")
        self.wb.close()

    def run(self):
        self.login()
        self.get_right_dates()
        self.parse_date_list()
        self.logout()


# 以下为几种主流浏览器驱动的路径，强烈建议使用chrome
path = r"C:\Users\rc431\Desktop\工时填报\chromedriver.exe"  # 前往http://npm.taobao.org/mirrors/chromedriver/下载对应版本
# path = r"C:\Users\rc431\Desktop\工时填报\IEDriverServer.exe" # ie
# path = r"C:\Users\rc431\Desktop\工时填报\geckodriver.exe" # firefox

user_dict = {
    "FC003441": "111111",
    "FC000982": "111111",
    "FC003563": "111111",
    "FC003036": "111111",
    "FC003057": "111111",
    "FC000891": "111111",
    "FC003629": "111111",
    "FC003132": "111111",
    "FC000662": "111111",
    "FC003945": "111111"
}

for i in user_dict:
    print(f"Now processing: {i}")
    s = AutoWHS(i, user_dict[i], "chrome", path)
    s.run()
    print(f"Complete: {i}")
    time.sleep(1)
     