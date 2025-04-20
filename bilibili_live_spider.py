from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from multiprocessing.dummy import Pool
from time import sleep, time
import os
import csv
import traceback

# 弹幕，礼物读取函数（改为动态 DOM 抓取）
def get_list(bro):
    uid_list,name_list, ct_list, danmaku_list = [], [], [], []
    gift_uname_list, gift_name_list, gift_count_list = [], [], []

    try:
        danmaku_items = bro.find_elements(By.XPATH, '//div[contains(@class, "danmaku-item")]')
        for item in danmaku_items:
            uid = item.get_attribute("data-uid")
            name = item.get_attribute("data-uname")
            ct = item.get_attribute("data-ct")
            danmaku = item.get_attribute("data-danmaku")
            if uid and ct and danmaku:
                uid_list.append(uid)
                name_list.append(name)
                ct_list.append(ct)
                danmaku_list.append(danmaku)
    except Exception as e:
        print("弹幕抓取出错：", e)

    try:
        gift_unames = bro.find_elements(By.XPATH, '//span[@class = "username v-bottom"]')
        gift_names = bro.find_elements(By.XPATH, '//span[@class = "gift-name v-bottom"]')
        gift_counts = bro.find_elements(By.XPATH, '//span[@class = "gift-total-count v-bottom"]')

        for i in range(min(len(gift_unames), len(gift_names), len(gift_counts))):
            gift_uname_list.append(gift_unames[i].text)
            gift_name_list.append(gift_names[i].text)
            gift_count_list.append(gift_counts[i].text)
    except Exception as e:
        print("礼物抓取出错：", e)

    return uid_list,name_list, ct_list, danmaku_list, gift_uname_list, gift_name_list, gift_count_list


# 去重函数
def remove_repeat(seq):
    once = seq[0]
    total = seq[1]
    try:
        cut_index = once.index(total[-1])
        once = once[cut_index + 1:]
        total.extend(once)
    except ValueError:
        total.extend(once)


# 清屏函数
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


# -----------------------提示用户输入部分--------------------------
total_danmaku_list = ['start']
total_gift_list = ['start']

url = input('请输入bilibili直播间地址：')
mode = input('选择模式，输入slow或fast。slow适用于600万以内人数直播间，fast适用于多于600万人数直播间：')
if mode =='slow':
    temp_num = 201
    refresh_time = 1
elif mode == 'fast':
    temp_num = 401
    refresh_time = 0.5
else:
    temp_num = 201
    refresh_time = 1
    print('模式错误，已默认设为slow模式！')

monitoring = input('选择在屏幕上输出以监视的是弹幕还是礼物信息。（弹幕输入d，礼物信息输入g）：')
if monitoring == 'd':
    command = r'print(total_danmaku_list)'
elif monitoring == 'g':
    command = r'print(total_gift_list)'
else:
    command = r'print(total_danmaku_list)'
    print('模式错误，已默认设置为弹幕监视！')

work_path = input('输入爬取数据保存的文件路径：（运行完成后文件存为danmaku.csv和gift.csv）：')
if os.path.exists(work_path):
    os.chdir(work_path)
else:
    os.makedirs(work_path)
    os.chdir(work_path)

run_time = int(input('输入运行时长（单位：秒数，若需要运行至直播间关闭，请输入0）：'))
if run_time == 0 or run_time < 0:
    run_time = 172800
    print('已设置为直播间关闭自动停止（最长48小时）')

# -----------------------正式运行部分--------------------------
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
service = Service('F:/download1/chromedriver-win64/chromedriver.exe')  # 修改为你的chromedriver路径
bro = webdriver.Chrome(service=service, options=options)

fp_danmaku = open('./danmaku.csv', 'a', encoding='utf-8-sig', newline='')
fp_gift = open('./gift.csv', 'a', encoding='utf-8-sig', newline='')
danmaku_writer = csv.writer(fp_danmaku)
gift_writer = csv.writer(fp_gift)
# 修改列名以匹配实际数据结构
danmaku_writer.writerow(['时间', '用户ID', '用户名', '弹幕内容'])
gift_writer.writerow(['用户名', '礼物名称', '数量'])

bro.get(url)
sleep(2)
try:
    iframe_tag = bro.find_element(By.XPATH, '//div[@class = "player"]//iframe')
    bro.switch_to.frame(iframe_tag)
    print("已切换到 iframe")
except NoSuchElementException:
    print("未找到 iframe，继续使用主页面")

start_time = time()

while True:
    uid_list, name_list, ct_list, danmaku_list, gift_uname_list, gift_name_list, gift_count_list = get_list(bro)
    # 修改数据组织方式
    once_danmaku_list = list(zip(ct_list, uid_list, name_list, danmaku_list))
    once_gift_list = list(zip(gift_uname_list, gift_name_list, gift_count_list))

    pool = Pool(2)
    pool.map(remove_repeat, [(once_danmaku_list, total_danmaku_list), (once_gift_list, total_gift_list)])

    clear()
    eval(command)

    # 检查弹幕数据写入
    try:
        if len(total_danmaku_list) >= temp_num:
            del total_danmaku_list[0]
            danmaku_writer.writerows(total_danmaku_list)
            print('\n------>弹幕进行了一次保存\n')
            total_danmaku_list = [total_danmaku_list[-1]]
    except Exception as e:
        print(f"弹幕写入异常: {e}")
        traceback.print_exc()

    # 检查礼物数据写入
    try:
        if len(total_gift_list) >= temp_num:
            del total_gift_list[0]
            gift_writer.writerows(total_gift_list)
            print('\n------>礼物信息进行了一次保存\n')
            total_gift_list = [total_gift_list[-1]]
    except Exception as e:
        print(f"礼物写入异常: {e}")
        traceback.print_exc()

    if time() - start_time > run_time:
        print('运行时长已到，等待程序结束中...')
        del total_danmaku_list[0]
        del total_gift_list[0]
        try:
            danmaku_writer.writerows(total_danmaku_list)
            gift_writer.writerows(total_gift_list)
        except Exception as e:
            print(f"结束时写入异常: {e}")
            traceback.print_exc()
        break

    try:
        bro.find_element(By.XPATH, '//div[@class = "bilibili-live-player-ending-panel-info"]')
        print('直播间已关闭，等待程序结束中...')
        del total_danmaku_list[0]
        del total_gift_list[0]
        try:
            danmaku_writer.writerows(total_danmaku_list)
            gift_writer.writerows(total_gift_list)
        except Exception as e:
            print(f"直播间关闭时写入异常: {e}")
            traceback.print_exc()
        break
    except NoSuchElementException:
        pass

    sleep(refresh_time)

bro.quit()
print('\n------>运行完成\n')
sleep(5)