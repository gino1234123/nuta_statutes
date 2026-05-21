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
  "Noto Serif TC"),
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
      #text(14pt, weight: "semibold")[
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
      #text(weight: "bold")[第#to-cjk(n)條]
      #par(leading: 1.2em, hanging-indent: 1em, first-line-indent: 1em)[#body]
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

== 法規之制定

#article()[
  法律應定名為法或條例。\
  法律名稱前應冠「國立台灣藝術大學學生會」。
]

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
  命令應依其性質，稱規則、細則、辦法或標準。\
  命令名稱前應冠「國立台灣藝術大學學生會」。
]

#article()[
  各機關依其於事務需求得訂定命令。\
  命令於訂定後應公布予全體會員，由其可合理取得資訊之管道為之。\
  命令於訂定後，應送學生議會備查。
]

#article()[
  應以法律規定之事項，不得以命令定之。
]

#article()[
  法律或命令之條文應分條書寫，冠以「第某條」字樣，並得下分為項、款、目。項不冠數字，款冠以一、二、三等數字，目冠以（一）、（二）、（三）等數字，並應加具標點符號。\
  前項所定之目再細分者，冠以1、2、3等數字，並稱為第某目之1、2、3。\
  法規內容繁複或條文較多者，得劃分為第某編、第某章、第某節
]

#article()[
  修正法規廢止少數條文時，得保留所廢條文之條次，並於其下加括弧，註明「刪除」二字。\
  修正法規增加少數條文時，得將增加之條文，列在適當條文之後，冠以前條「之一」、「之二」等條次。\
  廢止或增加編、章、節時，準用前二項之規定。
]

#article()[
  法規中應規定施行日期，或授權以命令規定施行日期。\
  法規中規定有施行日期，或授權以命令規定施行日期者，自所規訂之日起發生效力。
]

#article()[
  法規明定自公布或發布日施行者，自公布或發布之隔日起發生效力。
]

#article()[
  法規定有施行區域或授權以命令規定施行區域者，於該特定區域內發生效力。
]

== 法規之適用

#article()[
  法規對其他法規之同一事項，做特別規定者，應優先適用之。其他法規修正後，仍應優先適用。
]

#article()[
  法規對某事項，規定適用或準用其他法規之規定者，其他法規修正後，適用或準用修正後之法規。
]

#article()[
  各機關受理會員聲請許可案件，適用某法規時，除依照其性質應適用聲請時之法規外，如在處理程序終結前，某法規有變更者，適用變更後之新法規。\
  舊法規有利於當事人而新法規未廢除或禁止所聲請之事項者，適用舊法規。
]

#article()[
  法規因遭遇非常事故，一時不能適用者，得暫停適用其一部或全部。\
  法規停止或恢復適用之程序，準用本法有關法規廢止或制定之規定。
]

== 法規之修正與廢止

#article()[
  法律應視需求修正或廢止。\
  法律修正或廢止之程序，準用本法對法律制定之規定。\
  法律定有施行期限者，期滿當然廢止，不適用前項之規定，但應由會長公布之。
]

#article()[
  命令應視需求修正或廢止。\
  命令修正或廢止之程序，準用本法對命令訂定之規定。\
  命令定有施行期限者，期滿當然廢止，不適用前項之規定，但應由該命令之訂定機關公布之。
]

#article()[
  命令之原發布機關或主管機關已裁併者，其廢止或延長，由承受其業務之機關或其上級機關為之。
]

== 附則

#article()[
  本法自公布日施行。
]