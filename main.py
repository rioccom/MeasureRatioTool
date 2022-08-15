from math import dist, floor
import tkinter as tk
import tkinter.ttk as ttk
import pandas as pd
import numpy as np


class Application(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()
        self.master.geometry("800x350")
        self.master.title("比率測定")
        self.master.bind("<KeyPress>", self.key_event)  # 押下キー取得用

        self.hex_blu = "#0000ff"
        self.hex_red = "#ff0000"
        self.hex_yel = "#ff8c00"

        self.DF = pd.DataFrame()
        self.arrow = self.new_arrow()
        self.baseId = 0
        self.baseLength = 0

        self.line = None
        self.leng = None
        self.create_widgets()

    # ウィンドウ描画****************************************************
    # 全体
    def create_widgets(self):
        self.frame_main = tk.PanedWindow(self.master, orient="horizontal")
        self.frame_main.pack(expand=True, fill=tk.BOTH, side="left")

        pw1 = self.draw_pw1(self.frame_main)
        self.frame_main.add(pw1)
        pw2 = self.draw_pw2(self.frame_main)
        self.frame_main.add(pw2)

        self.reset()

    # 左側Column
    def draw_pw1(self, pw1):
        pw1 = tk.PanedWindow(pw1, bg="gray", orient="horizontal")
        self.canv1 = tk.Canvas(pw1, width=480, height=300, borderwidth=10)
        self.canv1.grid(row=0, column=2, padx=2, pady=2)
        self.canv1.bind("<Button-1>", self.dd_01click)
        self.canv1.bind("<B1-Motion>", self.dd_02drag)
        self.canv1.bind("<ButtonRelease-1>", self.dd_03drop)

        return pw1

    # 右側Column
    def draw_pw2(self, pw2):
        pw2 = tk.PanedWindow(pw2, bg="skyblue", orient="horizontal")

        # ①リセットボタン設置
        self.btnReset = ttk.Button(
            pw2,
            text="Reset (BackSpace)",
            width=20,
            style="MyWidget.TButton",
            command=self.reset,
        )
        self.btnReset.grid(row=0, column=0, padx=5, pady=2)

        # ②Applyボタン設置
        self.btnApply = ttk.Button(
            pw2,
            text="Apply (Enter)",
            width=20,
            style="MyWidget.TButton",
            command=self.apply,
        )
        self.btnApply.grid(row=1, column=0, padx=5, pady=2)

        # ③Treeviewの設置
        self.tree = ttk.Treeview(pw2, show="headings")
        # --設定
        self.tree["columns"] = ("id", "length", "ratio", "baseflg")
        self.tree.column("id", anchor="center", width=40)
        self.tree.column("length", anchor="center", width=50)
        self.tree.column("ratio", anchor="e", width=50)
        self.tree.column("baseflg", anchor="center", width=30)
        self.tree.heading("id", text="id", anchor="center")
        self.tree.heading("length", text="length", anchor="center")
        self.tree.heading("ratio", text="ratio", anchor="center")
        self.tree.heading("baseflg", text="-", anchor="center")
        self.tree.bind("<Double-Button-1>", self.doubleClick_row)
        # self.tree.bind("<<TreeviewSelect>>", self.select_row)
        # --DataFrameの値を取得
        self.updateTree_byDF()
        self.drawArrows_byDF()
        # --設置
        self.tree.grid(row=2, column=0, padx=5, pady=2)

        # ④ラベル
        self.label = tk.Label(
            pw2,
            bg="skyblue",
            text="*DoubleClick：select default length",
            font=("MSゴシック", "8"),
        )
        self.label.grid(row=3, column=0, padx=5, pady=2)

        return pw2

    # ************************************************************************

    # マウス･キー押下イベント*************************************************
    # 各種ショートカット
    def key_event(self, event):
        if event.keysym == "":
            pass
        elif event.keysym == "BackSpace":
            self.reset()
        elif event.keysym == "Return":
            self.apply()
        elif event.keysym == "p":
            self.printDF  # kesu

    # クリック
    def dd_01click(self, e):
        self.arrow["x1"] = e.x
        self.arrow["y1"] = e.y

    # ドラッグ
    def dd_02drag(self, e):
        if self.line:
            a = (self.arrow["x1"], self.arrow["y1"])
            b = (e.x, e.y)
            intDist = floor(dist(a, b))
            # arrow再描画
            self.canv1.coords(self.line, self.arrow["x1"], self.arrow["y1"], e.x, e.y)
            # テキスト再描画
            self.canv1.delete(self.leng)
            self.leng = self.canv1.create_text(
                (self.arrow["x1"] + e.x) / 2 + 10,
                (self.arrow["y1"] + e.y) / 2,
                text="(" + str(self.getRatio_onTemp(intDist)) + ")",
                anchor="w",
                fill=self.hex_yel,
                font=("Helvetica 10"),
            )
            self.arrow["length"] = intDist
        else:
            self.line = self.canv1.create_line(
                self.arrow["x1"],
                self.arrow["y1"],
                e.x,
                e.y,
                width=1,
                fill=self.hex_yel,
                arrow="both",
            )

    # ドロップ
    def dd_03drop(self, e):
        self.arrow["x2"] = e.x
        self.arrow["y2"] = e.y
        self.arrow["ratio"] = self.getRatio_onTemp(self.arrow["length"])

    # ダブルクリック
    def doubleClick_row(self, e):
        tree = e.widget
        self.baseId = tree.item(tree.focus())["values"][0]
        self.setBase_byId()
        self.updateTree_byDF()
        self.drawArrows_byDF()

    # 選択
    # def select_row(self, e):
    #    tree = e.widget
    #    selectedId = tree.item(tree.focus())["values"][0]
    #    self.setSelected_byId(selectedId)
    #    self.updateTree_byDF()
    #    self.drawArrows_byDF()

    # ratio計算
    def getRatio_onTemp(self, length):
        if length == 0:
            ratio = format(0, ".2f")
        elif self.baseLength == 0:
            ratio = format(1, ".2f")
        else:
            ratio = format(length / self.baseLength, ".2f")
        return ratio

    # ************************************************************************

    # 各処理用メソッド********************************************************
    # Resetボタン用イベント
    def reset(self):
        if self.line:
            self.canv1.delete(self.line)
            self.line = None
            self.canv1.delete(self.leng)
            self.leng = None
            self.arrow["length"] = 0
        else:
            if len(self.DF) == 0:
                pass
            else:
                maxId = self.DF["id"].max()
                self.DF = self.DF.drop(maxId)
                self.updateTree_byDF()
                self.drawArrows_byDF()
        self.getBaseLength_byDF()
        self.arrow = self.new_arrow()

    # Applyボタン用イベント
    def apply(self):
        if self.arrow["length"] == 0:
            pass
        else:
            record = pd.DataFrame([self.arrow])
            record.index = record["id"]

            if len(self.DF) == 0:
                self.DF = record
                self.DF.set_index("id")
            else:
                self.DF = pd.concat([self.DF, record])

            if self.line:
                self.reset()

            self.getBaseLength_byDF()
            self.setBase_byId()
            self.updateTree_byDF()
            self.drawArrows_byDF()
            self.new_arrow()

    # -----------------------------------------------------------
    ## 任意のデータを選択
    # def setSelected_byId(self, id):
    #    self.DF.loc[self.DF["color"]!=self.hex_red,"color"] = self.hex_blu
    #    if self.DF.at[id,"baseflg"]==1:
    #        self.DF.at[id, "color"] = self.hex_yel

    # 基準データの指定
    def setBase_byId(self):
        id = self.baseId

        self.DF["baseflg"] = int(0)
        self.DF["color"] = self.hex_blu

        self.DF.at[id, "baseflg"] = int(1)
        self.printDF  # kesu
        self.baseLength = self.DF.at[id, "length"]
        self.DF["ratio"] = [
            format(item / self.baseLength, ".2f") for item in self.DF["length"]
        ]
        self.DF.at[id, "color"] = self.hex_red

    # 基準lengthを取得
    def getBaseLength_byDF(self):
        self.baseLength = 0
        if len(self.DF) > 0:
            for row in self.DF.itertuples():
                if row.baseflg == 1:
                    self.baseId = row.id
                    self.baseLength = row.length
                    break

    # DFからTreeView更新
    def updateTree_byDF(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.DF.itertuples():
            getFlg = "★" if (row.baseflg == 1) else " "
            self.tree.insert(
                "", "end", values=(row.id, row.length, row.ratio, getFlg, row.color)
            )

    # DFに登録されたarrowを全て描画
    def drawArrows_byDF(self):
        self.canv1.delete("all")
        for row in self.DF.itertuples():
            self.canv1.create_line(
                row.x1,
                row.y1,
                row.x2,
                row.y2,
                width=1,
                fill=row.color,
                arrow="both",
            )
            self.canv1.create_text(
                (row.x1 + row.x2) / 2 + 10,
                (row.y1 + row.y2) / 2,
                text="(" + str(row.ratio) + ")",
                anchor="w",
                fill=row.color,
                font=("Helvetica 10"),
            )

    # 新規データ生成
    def new_arrow(self):
        maxId = len(self.DF)
        dic_arrow = {
            "id": maxId + 1,
            "x1": 0,
            "y1": 0,
            "x2": 0,
            "y2": 0,
            "length": 0,
            "color": self.hex_yel,
            "ratio": format(0, ".2f"),
            "baseflg": 1 if (len(self.DF) == 0) else 0,
        }
        return dic_arrow

    # デバッグ用
    def printDF(self):
        print("=========================")
        print(self.DF)

    # ************************************************************************


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()
