from math import dist, floor
import tkinter as tk
import tkinter.ttk as ttk
import pandas as pd
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps


class Application(tk.Frame):
    def __init__(self, master):

        self.DF = pd.DataFrame()
        self.hex_blu = "#0000ff"
        self.hex_red = "#ff0000"
        self.hex_yel = "#ff8c00"
        self.pw1_W = 600 #画面左側width
        self.pw1_H = 800 #画面左側height
        self.pw2_W = 220 #画面右側width
        self.baseId = 0
        self.baseLength = 0
        self.line = None
        self.leng = None
        self.filepath = "";
        self.dispImg = ImageTk.PhotoImage
        self.opacity = 30 #画像の不透明度

        super().__init__(master)
        self.pack()
        self.master.geometry(f"{self.pw1_W + self.pw2_W}x{self.pw1_H}")
        self.master.title("比率測定")
        self.master.bind('<Configure>', self.configure) #ウィンドウ位置同期用
        self.master.bind("<KeyPress>", self.key_event)  #ショートカットキー取得用

        self.master.upper = tk.Toplevel() #別ウィンドウ生成
        self.master.upper.wm_attributes("-topmost", True) #常に手前に表示
        self.master.upper.overrideredirect(True) #タイトル部分非表示
        self.master.upper.geometry(f"{self.pw1_W}x{self.pw1_H}")
        self.master.upper.canv2 = tk.Canvas(self.master.upper, background="#f0f0f0") 
        self.master.upper.canv2.pack(fill=tk.BOTH, expand=True)
        self.master.upper.wm_attributes("-transparentcolor", "#f0f0f0") #透過色設定

        self.create_widgets()
        self.arrow = self.new_arrow()

        # menubar作成
        menubar = tk.Menu(self)
        # menubar＞menu_file作成
        menu_file = tk.Menu(menubar, tearoff=False)
        menu_file.add_command(
            label="画像を開く", command=self.menu_OpenFile, accelerator="Ctrl+O"
        )
        menu_file.add_separator()  # 仕切り線
        menu_file.add_command(
            label="終了", command=self.master.destroy, accelerator="Ctrl+W"
        )
        menu_file.bind_all("<Control-o>", self.menu_OpenFile)
        menu_file.bind_all("<Control-w>", self.master.destroy)
        menubar.add_cascade(label="ファイル", menu=menu_file)
        # menubar設置
        self.master.config(menu=menubar)

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
        self.canv1 = tk.Canvas(pw1, width=self.pw1_W, height=self.pw1_H, borderwidth=0)
        self.canv1.grid(row=0, column=2, padx=0, pady=0)
        self.canv1.bind("<Button-1>", self.dd_01click)
        self.canv1.bind("<B1-Motion>", self.dd_02drag)
        self.canv1.bind("<ButtonRelease-1>", self.dd_03drop)
        self.canv1.bind("<Unmap>", self.unmap)
        self.canv1.bind("<Map>", self.map)

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

    # メニュー****************************************************************
    # ファイル選択ダイアログ
    def menu_OpenFile(self):
        self.filepath = filedialog.askopenfilename(
            title="ファイルを開く",
            filetypes=[
                ("Image file", ".png .jpg .tif"),
                ("PNG", ".png"),
                ("JPEG", ".jpg"),
            ],
            initialdir="./",
        )
        self.showImage()

    #画像をキャンバスサイズにリサイズして表示
    def showImage(self):
        if not self.filepath:
            return

        pilImg = Image.open(self.filepath)
        pilImg = ImageOps.pad(
            pilImg, (self.pw1_W, self.pw1_H), color=None
        )
        pilImg.putalpha(int((self.opacity/100)*255))
        self.dispImg = ImageTk.PhotoImage(image=pilImg)
        self.canv1.create_image(
            self.pw1_W / 2,
            self.pw1_H / 2,
            image=self.dispImg
        )
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
            self.printDF  #(仮)

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
            self.master.upper.canv2.coords(self.line, self.arrow["x1"], self.arrow["y1"], e.x, e.y)
            # テキスト再描画
            self.master.upper.canv2.delete(self.leng)
            self.leng = self.master.upper.canv2.create_text(
                (self.arrow["x1"] + e.x) / 2 + 10,
                (self.arrow["y1"] + e.y) / 2,
                text="(" + str(self.getRatio_onTemp(intDist)) + ")",
                anchor="w",
                fill=self.hex_yel,
                font=("Helvetica 10"),
            )
            self.arrow["length"] = intDist
        else:
            self.line = self.master.upper.canv2.create_line(
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
            self.master.upper.canv2.delete(self.line)
            self.line = None
            self.master.upper.canv2.delete(self.leng)
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
        self.master.upper.canv2.delete("all")
        for row in self.DF.itertuples():
            self.master.upper.canv2.create_line(
                row.x1,
                row.y1,
                row.x2,
                row.y2,
                width=1,
                fill=row.color,
                arrow="both",
            )
            self.master.upper.canv2.create_text(
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

    def unmap(self, event): 
        self.master.upper.withdraw() #ウィンドウを非表示にする

    def map(self, event):
        self.lift() #ウィンドウを上に移動
        self.master.upper.wm_deiconify()
        self.master.upper.attributes("-topmost", True) #一番上になるよう再設定

    def configure(self, event): #透明キャンバスウィンドウサイズの調節
        x, y = self.canv1.winfo_rootx(), self.canv1.winfo_rooty()
        self.master.upper.geometry(f"{self.pw1_W}x{self.pw1_H-5}+{x}+{y}")

    # デバッグ用
    def printDF(self):
        print("=========================")
        print(self.DF)
    # ************************************************************************

def main():
    root = tk.Tk()
    root.resizable(0,0)
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
