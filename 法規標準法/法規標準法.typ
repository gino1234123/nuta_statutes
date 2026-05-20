#set page(
  paper: "a4",
  margin: (
    x: 3cm,
    y: 2.5cm,
  ),
)

#set text(
  font: (
  (name: "Times New Roman", covers: "latin-in-cjk"),
  "TW-Kai"),
  size: 12pt,
  lang: "zh",
  region: "TW"
)


#let chapter-counter = counter("chapter")
#let article-counter = counter("article")

// 阿拉伯數字轉中文小寫（1..9999）
#let to-cjk(n) = {
  let d = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")
  if n <= 0 {
    "零"
  } else if n < 10 {
    d.at(n)
  } else if n < 100 {
    let t = calc.floor(n / 10)
    let o = calc.rem(n, 10)
    if t == 1 {
      if o == 0 { "十" } else { "十" + d.at(o) }
    } else {
      if o == 0 { d.at(t) + "十" } else { d.at(t) + "十" + d.at(o) }
    }
  } else if n < 1000 {
    let h = calc.floor(n / 100)
    let r = calc.rem(n, 100)
    if r == 0 {
      d.at(h) + "百"
    } else if r < 10 {
      d.at(h) + "百零" + d.at(r)
    } else {
      d.at(h) + "百" + to-cjk(r)
    }
  } else if n < 10000 {
    let th = calc.floor(n / 1000)
    let r = calc.rem(n, 1000)
    if r == 0 {
      d.at(th) + "千"
    } else if r < 100 {
      d.at(th) + "千零" + to-cjk(r)
    } else {
      d.at(th) + "千" + to-cjk(r)
    }
  } else {
    str(n)
  }
}

// 文件標題
#show heading.where(level: 1): it => {
  align(center)[
    #text(18pt, weight: "bold")[
      #it.body
    ]
  ]
}

// 章
#show heading.where(level: 2): it => {
  context {
    let n = chapter-counter.get().first() + 1

    chapter-counter.step()
    
    v(2em)

    align(center)[
      #text(14pt, weight: "bold")[
        第#to-cjk(n)章　#it.body
      ]
    ]

  }
}

// 條（建議使用 #article[...]，可同條換行/分段）
#let article(body) = {
  context {
    let n = article-counter.get().first() + 1
    article-counter.step()
    v(1.5em)
    block[
      #text[第#to-cjk(n)條]
      #par(hanging-indent: 1em, first-line-indent: 1em)[#body]
    ]
  }
}

= 國立臺灣藝術大學學生會法規標準法

== 總則

#article()[
  國立臺灣藝術大學學生會（以下簡稱本會）法規之制定、施行、適用、修正及廢止，除組織章程規定外，依本法之規定。
]

#article()[
  本會之法規，依其階層，分法律及命令。\
  法律不得牴觸組織章程，命令不得牴觸組織章程或法律，下級機關訂定之命令不得牴觸上級機關之命令。
]

#article()[
  法律應定名為法或條例。\
  法律名稱前應冠「國立台灣藝術大學學生會」。
]

#article()[
  本法所稱之命令，指由各機關依其於事務需求，所訂定者。\
  命令應依其性質，稱規則、細則、辦法或標準。\
  命令名稱前應冠「國立台灣藝術大學學生會」。
]

== 法規之制定

#article()[
  法律應由學生議會審議通過，並依組織章程之規定，由會長公布之。\
  公布法律應由全體會員可合理取得資訊之管道為之。
]

#article()[
  下列事項應以法律定之：\
  一、組織章程或法律有明文規定，應以法律定之者。\
  二、關於會員之權利、義務者。\
  三、其他重要事項之應以法律定之者。\
]

#article()[
  應以法律規定之事項，不得以命令定之。
]

#article()[
  命令於訂定後，應送學生議會
]