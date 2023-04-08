from random import randint
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QAbstractItemView, QMessageBox
from PyQt5 import QtWidgets, QtCore
import sys, os
import cv2 
import pymysql
import json
import numpy as np

class sqlUtils():
    def __init__(self):
        self.db = self.connectToMySQL()
        self.cursor = self.db.cursor()

    def connectToMySQL(self):
        try:
            db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, database='vg100k')
            print('连接成功！')
            return db
        except:
            print('连接失败!')

    def search(self, sop, keyword):
        if(sop=='subject' or sop=='object'):
            sql =  "SELECT DISTINCT image_id \
                    FROM rels_mysql \
                    WHERE SUBSTRING_INDEX(`{}`,',', 1) LIKE '%{}%'".format(str(sop), str(keyword))
        elif sop=='predicate':
            sql =  "SELECT DISTINCT image_id \
                    FROM rels_mysql \
                    WHERE predicate = {} OR predicate = {}".format(str(sop).lower(), str(sop).upper())
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        image_list = []
        for result in results:
            image_list.append(result[0])
        return image_list
    
    def acuurateSearch(self, sub, pred, ob):
        sql =  "SELECT DISTINCT image_id \
                FROM rels_mysql \
                WHERE SUBSTRING_INDEX(`subject`,',', 1) LIKE '%{}%' AND predicate = '{}' AND SUBSTRING_INDEX(`object`,',', 1) LIKE '%{}%'".format(str(sub), str(pred), str(ob))
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        image_list = []
        for result in results:
            image_list.append(result[0])
        return image_list

    def getRelationshipsByImageID(self, image_id):
        sql = "SELECT `subject`, object, predicate \
               FROM rels_mysql \
               WHERE image_id = {}".format(image_id)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        rels = []
        for result in results:
            rels.append({'subject':result[0], 'predicate': result[2], 'object': result[1]})
        return rels

class PicViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_dir = 'F:\\VG_100K'
        self.initializeUI()
    
    def initializeUI(self):
        self.setGeometry(200,200,1500,750)
        self.setWindowTitle("Viewer")
        self.setUpWindow()
        self.show()

    def setUpWindow(self):
        # 显示图片的label
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setObjectName("ImageLabel")
        self.image_label.move(300, 0)
        self.image_label.resize(1000, 800)

        # 显示图片名字的列表
        self.image_list = QtWidgets.QListWidget(self)
        self.image_list.setObjectName("ImageList")
        self.image_list.move(30, 180)
        self.image_list.resize(200 ,500)

        self.image_names = os.listdir('images')  #后续改成mysql查询结果
        for image_name in self.image_names:
            self.list_item = QtWidgets.QListWidgetItem()
            self.list_item.setText(image_name)
            self.image_list.addItem(self.list_item)

        self.image_list.itemClicked.connect(self.listItemClicked)
        # for item in self.image_list.items():
        #     if item.isSelected():
        #         print(item.text)

        # 连接数据库和返回查询结果
        self.db = sqlUtils()

        self.res = []
        self.subject_label = QtWidgets.QLabel(self)
        self.subject_label.move(10,10)
        self.subject_label.setText("Subject")
        self.query_text = QtWidgets.QLineEdit(self)
        self.query_text.move(90, 10)
        self.query_text.resize(150, 30)
        search_results = []
        self.query_text.returnPressed.connect(lambda:self.searchImage(self.db, self.query_text.text(), search_results))

        self.pred_label = QtWidgets.QLabel(self)
        self.pred_label.move(10,50)
        self.pred_label.setText("Predicate")
        self.pred_query_text = QtWidgets.QLineEdit(self)
        self.pred_query_text.move(90, 50)
        self.pred_query_text.resize(150, 30)
        self.pred_query_text.returnPressed.connect(lambda:self.searchImage(self.db, self.query_text.text(), search_results))

        self.object_label = QtWidgets.QLabel(self)
        self.object_label.move(10,90)
        self.object_label.setText("Object")
        self.object_query_text = QtWidgets.QLineEdit(self)
        self.object_query_text.move(90, 90)
        self.object_query_text.resize(150, 30)
        self.object_query_text.returnPressed.connect(lambda:self.searchImage(self.db, self.query_text.text(), search_results))

        # accurate search button
        self.search_button = QtWidgets.QPushButton(self)
        self.search_button.setText("精确")
        self.search_button.move(15,130)
        self.search_button.clicked.connect(self.accurateSearchButtonPushed)
        # fuzzy search button
        self.search_button = QtWidgets.QPushButton(self)
        self.search_button.setText("模糊")
        self.search_button.move(135,130)
        self.search_button.clicked.connect(self.fuzzySearchButtonPushed)

        # 显示关系的列表
        self.rel_list = QtWidgets.QListWidget(self)
        self.rel_list.setObjectName("ImageList")
        self.rel_list.move(1200, 50)
        self.rel_list.resize(300 ,650)

        self.rels = []
        self.rel_list.itemClicked.connect(self.relListItemClicked)
        self.rel_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def fuzzySearchButtonPushed(self):
        print("sub:", self.query_text.text())
        print("pred:", self.pred_query_text.text())
        print("ob:", self.object_query_text.text())
        subject = self.query_text.text()
        pred = self.pred_query_text.text()
        object = self.object_query_text.text()
        sub_res = []
        pred_res = []
        ob_res = []
        print('searching...')
        if(subject != ''):
            sub_res = self.db.search('subject', subject)
        if(pred != ''):
            pred_res = self.db.search('predicate', pred)
        if(object != ''):
            ob_res = self.db.search('object', object)
        self.res = list(set(sub_res).intersection(set(pred_res).intersection(set(ob_res))))
        print(self.res)
        self.updateListItems(self.res)
        
    def accurateSearchButtonPushed(self):
        print("sub:", self.query_text.text())
        print("pred:", self.pred_query_text.text())
        print("ob:", self.object_query_text.text())
        subject = self.query_text.text()
        pred = self.pred_query_text.text()
        object = self.object_query_text.text()
        if(subject=='' or pred=='' or object==''):
            QMessageBox.warning(self,"warning","精确搜索条件不能为空，检查后重新输入", QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
        else:
            print('searching...')
            self.res = self.db.acuurateSearch(subject, pred, object)
            print(self.res)
            self.updateListItems(self.res)

    def listItemClicked(self, item):
        print(item.text())
        self.showImage(item.text())
        self.updateRelListItems(item.text())

    def relListItemClicked(self, item):
        # rel_idx = self.rel_list.currentIndex().row()
        rel_chosen_idx = self.rel_list.selectedIndexes()
        all_selected_rels = []
        for rel_idx in rel_chosen_idx:
            idx = rel_idx.row()
            print(idx)
            rel = self.rels[idx]
            subject_json = json.loads(rel['subject'])
            subject_name = subject_json['name']
            subject_box_x = subject_json['x']
            subject_box_y = subject_json['y']
            subject_box_w = subject_json['w']
            subject_box_h = subject_json['h']
            predicate = rel['predicate']
            object_json = json.loads(rel['object'])
            object_name = object_json['name']
            object_box_x = object_json['x']
            object_box_y = object_json['y']
            object_box_w = object_json['w']
            object_box_h = object_json['h']

            s_x1 = subject_box_x
            s_y1 = subject_box_y
            s_x2 = subject_box_x + subject_box_w
            s_y2 = subject_box_y + subject_box_h

            o_x1 = object_box_x
            o_y1 = object_box_y
            o_x2 = object_box_x + object_box_w
            o_y2 = object_box_y + object_box_h

            all_selected_rels.append([s_x1, s_y1, s_x2, s_y2, o_x1, o_y1, o_x2, o_y2, subject_name, object_name, predicate])

        image_id = self.image_list.currentItem().text()
        cv_image = cv2.imread(self.image_dir+ '\\'+ image_id+ '.jpg')
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        for rel in all_selected_rels:
            s_x1 = rel[0]
            s_y1 = rel[1]
            s_x2 = rel[2]
            s_y2 = rel[3]
            o_x1 = rel[4]
            o_y1 = rel[5]
            o_x2 = rel[6]
            o_y2 = rel[7]
            subject_name = rel[8]
            object_name = rel[9]
            predicate = rel[10]
            r = np.random.randint(0, 255)
            g = np.random.randint(0, 255)
            b = np.random.randint(0, 255)
            cv2.rectangle(cv_image, (int(s_x1), int(s_y1)), (int(s_x2), int(s_y2)), (r, g, b), thickness=2)
            cv2.rectangle(cv_image, (int(o_x1), int(o_y1)), (int(o_x2), int(o_y2)), (r, g, b), thickness=2)
            cv2.putText(cv_image, subject_name + ' ' + predicate, (int(s_x1), int(s_y1)), cv2.FONT_HERSHEY_COMPLEX, 1, (r, g, b), 2)
            cv2.putText(cv_image, object_name, (int(o_x1), int(o_y1)), cv2.FONT_HERSHEY_COMPLEX, 1, (r, g, b), 2)
        height, width, channels = cv_image.shape
        bytes_per_line = width * channels
        converted_Qt_image = QImage(cv_image, width, height, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(converted_Qt_image)
        self.image_label.setPixmap(pix)

    def showImage(self, img_name):
        cv_image = cv2.imread(self.image_dir+ '\\'+ img_name+ '.jpg')
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        # cv2.rectangle(cv_image, (30,30), (0, 0), (255, 0, 0), thickness=2)
        height, width, channels = cv_image.shape
        bytes_per_line = width * channels
        converted_Qt_image = QImage(cv_image, width, height, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(converted_Qt_image)
        self.image_label.setPixmap(pix)

    #def drawBBox(self, rel)
    def searchImage(self, db, keyword, result):
        result = db.search(keyword)
        print(result)
        # Update list items
        self.updateListItems(result)
    
    def updateListItems(self, search_results):
        # 后续改成mysql查询结果
        self.image_list.clear()
        for image_name in search_results:
            list_item = QtWidgets.QListWidgetItem()
            list_item.setText(image_name)
            self.image_list.addItem(list_item)
        
    def updateRelListItems(self, image_id):
        self.rel_list.clear()
        rels = self.db.getRelationshipsByImageID(image_id)
        self.rels = rels
        for rel in rels:
            subject_json = json.loads(rel['subject'])
            subject = subject_json['name']
            predicate = rel['predicate']
            object_json = json.loads(rel['object'])
            object = object_json['name']
            list_item = QtWidgets.QListWidgetItem()
            list_item.setText("{}-{}-{}".format(subject, predicate, object))
            self.rel_list.addItem(list_item)
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PicViewer()
    sys.exit(app.exec_())