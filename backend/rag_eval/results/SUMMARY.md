# RAG evaluation summary (2026-11-28)

Counts are small (tens of questions): differences of a few points are within noise.

## Retrieval tier
| config | chunks | mode | rerank | n | Hit@1 | Hit@3 | Hit@5 | MRR@5 | embed ms p50/p95 | search ms p50/p95 | total ms p50/p95 | date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dense-article [dev] | article | dense | - | 41 | 0.463 | 0.585 | 0.683 | 0.534 | 234/277 | 13/57 | 249/392 | 2026-11-26 |
| dense-fixed [dev] | fixed | dense | - | 41 | 0.366 | 0.585 | 0.585 | 0.472 | 227/347 | 6/9 | 234/356 | 2026-11-26 |
| dense-s256 [dev] | article_s256 | dense | - | 41 | 0.366 | 0.585 | 0.610 | 0.464 | 237/306 | 7/10 | 244/313 | 2026-11-26 |
| hybrid-article-full [dev] | article | hybrid | llm | 41 | 0.756 | 0.902 | 0.927 | 0.831 | 257/395 | 2043/2515 | 4494/5262 | 2026-11-26 |
| hybrid-article-llmrerank [dev] | article | hybrid | llm | 41 | 0.854 | 0.902 | 0.902 | 0.878 | 242/457 | 3720/5021 | 4041/5272 | 2026-11-26 |
| hybrid-article-minirerank [dev] | article | hybrid | llm | 41 | 0.732 | 0.902 | 0.902 | 0.817 | 235/375 | 1984/2562 | 2217/2848 | 2026-11-26 |
| hybrid-article-planner [dev] | article | hybrid | - | 41 | 0.585 | 0.732 | 0.805 | 0.669 | 255/337 | 13/24 | 2353/2956 | 2026-11-26 |
| hybrid-article [dev] | article | hybrid | - | 41 | 0.585 | 0.780 | 0.829 | 0.674 | 228/374 | 15/30 | 243/387 | 2026-11-26 |
| hybrid-article-rrfk100 [dev] | article | hybrid | - | 41 | 0.585 | 0.780 | 0.829 | 0.674 | 244/301 | 9/11 | 253/310 | 2026-11-26 |
| hybrid-article-rrfk20 [dev] | article | hybrid | - | 41 | 0.561 | 0.756 | 0.829 | 0.659 | 234/293 | 9/12 | 244/303 | 2026-11-26 |
| hybrid-article-rrfk40 [dev] | article | hybrid | - | 41 | 0.585 | 0.780 | 0.829 | 0.674 | 233/284 | 9/14 | 243/299 | 2026-11-26 |
| hybrid-fixed [dev] | fixed | hybrid | - | 41 | 0.488 | 0.683 | 0.707 | 0.578 | 236/282 | 9/13 | 246/292 | 2026-11-26 |
| hybrid-s256 [dev] | article_s256 | hybrid | - | 41 | 0.488 | 0.707 | 0.780 | 0.612 | 231/258 | 10/13 | 239/269 | 2026-11-26 |
| sparse-article [dev] | article | sparse | - | 41 | 0.439 | 0.805 | 0.878 | 0.622 | 235/270 | 10/19 | 249/283 | 2026-11-26 |
| sparse-fixed [dev] | fixed | sparse | - | 41 | 0.439 | 0.732 | 0.780 | 0.568 | 235/322 | 5/7 | 240/330 | 2026-11-26 |
| sparse-s256 [dev] | article_s256 | sparse | - | 41 | 0.390 | 0.780 | 0.878 | 0.583 | 233/298 | 6/10 | 241/304 | 2026-11-26 |
| hybrid-article-cohere-pro [dev] | article | hybrid | cohere | 41 | 0.707 | 0.902 | 0.902 | 0.801 | 363/623 | 753/909 | 1151/1412 | 2026-11-27 |
| hybrid-article-cohere [dev] | article | hybrid | cohere | 41 | 0.732 | 0.902 | 0.902 | 0.813 | 364/554 | 749/847 | 1114/1398 | 2026-11-27 |
| hybrid-vbpl-cohere [dev] | vbpl | hybrid | cohere | 41 | 0.707 | 0.878 | 0.878 | 0.789 | 372/524 | 784/921 | 1175/1383 | 2026-11-27 |
| hybrid-vbpl-full-cohere-expand [dev] | vbpl | hybrid | cohere | 41 | 0.707 | 0.854 | 0.878 | 0.783 | 340/569 | 874/1319 | 3680/4817 | 2026-11-27 |
| hybrid-vbpl-full-cohere [dev] | vbpl | hybrid | cohere | 41 | 0.707 | 0.878 | 0.878 | 0.789 | 377/558 | 918/1119 | 3550/4691 | 2026-11-27 |
| hybrid-vbpl [dev] | vbpl | hybrid | - | 41 | 0.463 | 0.683 | 0.829 | 0.595 | 323/623 | 18/39 | 341/644 | 2026-11-27 |
| ab-planner-off [dev] | vbpl | hybrid | cohere | 41 | 0.707 | 0.878 | 0.878 | 0.789 | 354/535 | 770/903 | 1121/1322 | 2026-11-28 |
| ab-planner-on [dev] | vbpl | hybrid | cohere | 41 | 0.707 | 0.902 | 0.902 | 0.801 | 345/519 | 859/1037 | 3750/4409 | 2026-11-28 |
| hybrid-vbpl-full-cohere-expand [dev] | vbpl | hybrid | cohere | 41 | 0.732 | 0.927 | 0.927 | 0.825 | 344/557 | 863/1024 | 3969/4373 | 2026-11-28 |
| hybrid-vbpl-full-cohere-expand [test] | vbpl | hybrid | cohere | 40 | 0.725 | 0.900 | 0.925 | 0.806 | 342/570 | 863/1036 | 3720/4546 | 2026-11-28 |

## Generation tier
`answer correct`: an LLM judge compares each answerable question with its gold answer.
`rerank fallbacks` of `-` in a rerank run: not recorded, so the rerank may have been
skipped on some questions (rate limit).
`unsupported ref`: a document number or article that neither the retrieved passages nor
the question contain. Not proof of fabrication; undefined without retrieval.
`OOC refused (hand)`: set `refused` on each out-of-corpus row of the result file first.

| config | answered | answer correct | partial/incorrect/refused | errors | truncated | cit. precision | cit. recall | unsupported ref | unknown doc | needs review | OOC no-cite | OOC refused (hand) | TTFT ms p50/p95 | end-to-end ms p50/p95 | tokens in/out | rerank fallbacks | date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| norag [dev] | 47 | 0.512 | 13/6/1 | 0 | 0 | - | 0.000 | - | 0.362 | 14 | 1.000 | 0.000 | 9653/17828 | 13271/20630 | 8517/80576 | - | 2026-11-26 |
| rag-full-incorpus [dev] | 41 | 0.659 | 11/0/3 | 0 | 0 | 0.690 | 0.890 | 0.000 | 0.024 | 2 | - | - | 1896/4401 | 9061/13435 | 92912/16360 | - | 2026-11-26 |
| rag-full-ooc [dev] | 6 | - | - | 0 | 0 | - | - | 0.000 | 0.000 | 0 | 0.500 | 1.000 | 1239/2227 | 7866/9507 | 9759/1324 | - | 2026-11-26 |
| rag-hybrid-article [dev] | 47 | 0.610 | 10/0/6 | 0 | 0 | 0.717 | 0.817 | 0.000 | 0.021 | 0 | 0.500 | 1.000 | 1884/3442 | 4273/7493 | 110840/17715 | - | 2026-11-26 |
| rag-app-cohere [dev] | 47 | 0.683 | 9/0/4 | 0 | 0 | 0.693 | 0.846 | 0.000 | 0.021 | 2 | 0.500 | - | 2109/4924 | 7745/13770 | 111485/19579 | - | 2026-11-27 |
| rag-app-cohere-vbpl-expand [dev] | 47 | 0.707 | 8/1/3 | 0 | 0 | 0.694 | 0.837 | 0.000 | 0.021 | 4 | 0.500 | - | 2234/5174 | 7441/11694 | 247983/21660 | - | 2026-11-27 |
| rag-app-cohere-vbpl [dev] | 47 | 0.707 | 7/0/5 | 0 | 0 | 0.625 | 0.789 | 0.000 | 0.021 | 2 | 0.667 | - | 1884/3848 | 6710/11310 | 119780/17768 | - | 2026-11-27 |
| ab-expand-off [dev] | 47 | 0.732 | 8/2/1 | 0 | 0 | 0.671 | 0.862 | 0.000 | 0.021 | 5 | 0.500 | - | 1932/3996 | 8010/11678 | 134515/18722 | 0 | 2026-11-28 |
| ab-expand-on [dev] | 47 | 0.780 | 6/1/2 | 0 | 0 | 0.667 | 0.870 | 0.000 | 0.021 | 2 | 0.500 | - | 1862/5894 | 8158/13976 | 246434/20841 | 0 | 2026-11-28 |
| rag-app-cohere-vbpl-expand [dev] | 47 | 0.659 | 8/4/2 | 0 | 0 | 0.677 | 0.862 | 0.000 | 0.021 | 4 | 0.667 | - | 2070/4168 | 7815/11312 | 247677/19282 | - | 2026-11-28 |
| rag-app-cohere-vbpl-expand [test] | 44 | 0.800 | 6/2/0 | 0 | 0 | 0.700 | 0.887 | 0.000 | 0.023 | 3 | 0.500 | - | 2165/4496 | 7845/11876 | 218114/17350 | 0 | 2026-11-28 |

## Error analysis (retrieval misses)

### dense-article [dev]

- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q016` [wrong_document] Tôi đang chuẩn bị triển khai hóa đơn điện tử cho doanh nghiệp. Chính phủ sẽ quy định những vấn đề nào liên quan đến hóa đơn điện tử? -> gold [['luat-quan-ly-thue-108-2025-qh15', 26]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `h08` [right_doc_wrong_article] Muốn thành lập công ty cổ phần thì tối thiểu phải có bao nhiêu cổ đông? -> gold [['luat-doanh-nghiep-59-2020-qh14', 111]]
- `q017` [wrong_document] Công ty tôi kinh doanh hàng hóa thuộc diện không phải chịu thuế GTGT. Thuế GTGT đầu vào có được khấu trừ hoặc đề nghị hoàn không, và trường hợp áp dụng thuế suất 0% có khác không? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q045` [wrong_document] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q055` [wrong_document] Tôi là cổ đông của một công ty. Tôi có thể đứng tên góp vốn thay cho người khác không? -> gold [['nghi-dinh-296-2026-nd-cp', 1]]

### dense-fixed [dev]

- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `q016` [wrong_document] Tôi đang chuẩn bị triển khai hóa đơn điện tử cho doanh nghiệp. Chính phủ sẽ quy định những vấn đề nào liên quan đến hóa đơn điện tử? -> gold [['luat-quan-ly-thue-108-2025-qh15', 26]]
- `q021` [right_doc_wrong_article] Công ty tôi đang nợ một doanh nghiệp bị cưỡng chế thuế, đồng thời được doanh nghiệp đó giao giữ một số tài sản. Khi nào cơ quan thuế có thể yêu cầu tôi nộp tiền hoặc giao tài sản để thi hành quyết định cưỡng chế? -> gold [['nghi-dinh-252-2026-nd-cp', 70]]
- `q029` [right_doc_wrong_article] Tôi là cá nhân cư trú kinh doanh. Tỷ lệ thuế tính trên doanh thu chịu thuế được xác định theo căn cứ nào? -> gold [['nghi-dinh-253-2026-nd-cp', 45]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q002` [wrong_document] Doanh nghiệp tôi nhập khẩu máy móc, vật tư phục vụ nghiên cứu và khai thác dầu khí, hoặc nhập máy bay, tàu thuyền để làm tài sản cố định hay thuê từ nước ngoài. Những trường hợp nào thuộc diện không chịu thuế giá trị gia tăng? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]
- `h11` [wrong_document] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q017` [wrong_document] Công ty tôi kinh doanh hàng hóa thuộc diện không phải chịu thuế GTGT. Thuế GTGT đầu vào có được khấu trừ hoặc đề nghị hoàn không, và trường hợp áp dụng thuế suất 0% có khác không? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]

### dense-s256 [dev]

- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q001` [right_doc_wrong_article] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q016` [wrong_document] Tôi đang chuẩn bị triển khai hóa đơn điện tử cho doanh nghiệp. Chính phủ sẽ quy định những vấn đề nào liên quan đến hóa đơn điện tử? -> gold [['luat-quan-ly-thue-108-2025-qh15', 26]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `q024` [wrong_document] Công ty tôi ở Việt Nam ký hợp đồng mua dịch vụ của một doanh nghiệp nước ngoài. Trong trường hợp phải nộp thuế thay, bên nào được xác định là người nộp thuế? -> gold [['nghi-dinh-320-2025-nd-cp', 2]]
- `q029` [right_doc_wrong_article] Tôi là cá nhân cư trú kinh doanh. Tỷ lệ thuế tính trên doanh thu chịu thuế được xác định theo căn cứ nào? -> gold [['nghi-dinh-253-2026-nd-cp', 45]]
- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q017` [wrong_document] Công ty tôi kinh doanh hàng hóa thuộc diện không phải chịu thuế GTGT. Thuế GTGT đầu vào có được khấu trừ hoặc đề nghị hoàn không, và trường hợp áp dụng thuế suất 0% có khác không? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]

### hybrid-article-full [dev]

- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q059` [right_doc_wrong_article] Tôi đăng ký vốn công ty cao hơn số tiền thực góp, đồng thời định giá tài sản đưa vào góp vốn cao hơn giá trị thực thì có vi phạm điều cấm nào không? -> gold [['luat-doanh-nghiep-59-2020-qh14', 16]]

### hybrid-article-llmrerank [dev]

- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article-minirerank [dev]

- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article-planner [dev]

- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `q059` [right_doc_wrong_article] Tôi đăng ký vốn công ty cao hơn số tiền thực góp, đồng thời định giá tài sản đưa vào góp vốn cao hơn giá trị thực thì có vi phạm điều cấm nào không? -> gold [['luat-doanh-nghiep-59-2020-qh14', 16]]
- `h11` [wrong_document] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q016` [wrong_document] Tôi đang chuẩn bị triển khai hóa đơn điện tử cho doanh nghiệp. Chính phủ sẽ quy định những vấn đề nào liên quan đến hóa đơn điện tử? -> gold [['luat-quan-ly-thue-108-2025-qh15', 26]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q017` [right_doc_wrong_article] Công ty tôi kinh doanh hàng hóa thuộc diện không phải chịu thuế GTGT. Thuế GTGT đầu vào có được khấu trừ hoặc đề nghị hoàn không, và trường hợp áp dụng thuế suất 0% có khác không? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article [dev]

- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q042` [right_doc_wrong_article] Ngoài các trường hợp bắt buộc phải đối thoại, doanh nghiệp có thể tổ chức đối thoại thêm khi nào và cần căn cứ vào đâu? -> gold [['nghi-dinh-145-2020-nd-cp', 37]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article-rrfk100 [dev]

- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q042` [right_doc_wrong_article] Ngoài các trường hợp bắt buộc phải đối thoại, doanh nghiệp có thể tổ chức đối thoại thêm khi nào và cần căn cứ vào đâu? -> gold [['nghi-dinh-145-2020-nd-cp', 37]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article-rrfk20 [dev]

- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q042` [right_doc_wrong_article] Ngoài các trường hợp bắt buộc phải đối thoại, doanh nghiệp có thể tổ chức đối thoại thêm khi nào và cần căn cứ vào đâu? -> gold [['nghi-dinh-145-2020-nd-cp', 37]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article-rrfk40 [dev]

- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q042` [right_doc_wrong_article] Ngoài các trường hợp bắt buộc phải đối thoại, doanh nghiệp có thể tổ chức đối thoại thêm khi nào và cần căn cứ vào đâu? -> gold [['nghi-dinh-145-2020-nd-cp', 37]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-fixed [dev]

- `q017` [right_doc_wrong_article] Công ty tôi kinh doanh hàng hóa thuộc diện không phải chịu thuế GTGT. Thuế GTGT đầu vào có được khấu trừ hoặc đề nghị hoàn không, và trường hợp áp dụng thuế suất 0% có khác không? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]
- `q029` [right_doc_wrong_article] Tôi là cá nhân cư trú kinh doanh. Tỷ lệ thuế tính trên doanh thu chịu thuế được xác định theo căn cứ nào? -> gold [['nghi-dinh-253-2026-nd-cp', 45]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `q059` [right_doc_wrong_article] Tôi đăng ký vốn công ty cao hơn số tiền thực góp, đồng thời định giá tài sản đưa vào góp vốn cao hơn giá trị thực thì có vi phạm điều cấm nào không? -> gold [['luat-doanh-nghiep-59-2020-qh14', 16]]
- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q027` [right_doc_wrong_article] Công ty tôi là doanh nghiệp Việt Nam, có hoạt động kinh doanh ở nước ngoài và đã nộp thuế thu nhập tại nước sở tại. Khi tính thuế ở Việt Nam, khoản thuế đã nộp ở nước ngoài được xử lý thế nào? -> gold [['luat-thue-tndn-67-2025-qh15', 3]]
- `q055` [wrong_document] Tôi là cổ đông của một công ty. Tôi có thể đứng tên góp vốn thay cho người khác không? -> gold [['nghi-dinh-296-2026-nd-cp', 1]]
- `q001` [right_doc_wrong_article] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-s256 [dev]

- `q042` [right_doc_wrong_article] Ngoài các trường hợp bắt buộc phải đối thoại, doanh nghiệp có thể tổ chức đối thoại thêm khi nào và cần căn cứ vào đâu? -> gold [['nghi-dinh-145-2020-nd-cp', 37]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q055` [wrong_document] Tôi là cổ đông của một công ty. Tôi có thể đứng tên góp vốn thay cho người khác không? -> gold [['nghi-dinh-296-2026-nd-cp', 1]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### sparse-article [dev]

- `q059` [right_doc_wrong_article] Tôi đăng ký vốn công ty cao hơn số tiền thực góp, đồng thời định giá tài sản đưa vào góp vốn cao hơn giá trị thực thì có vi phạm điều cấm nào không? -> gold [['luat-doanh-nghiep-59-2020-qh14', 16]]
- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h11` [wrong_document] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]

### sparse-fixed [dev]

- `q059` [right_doc_wrong_article] Tôi đăng ký vốn công ty cao hơn số tiền thực góp, đồng thời định giá tài sản đưa vào góp vốn cao hơn giá trị thực thì có vi phạm điều cấm nào không? -> gold [['luat-doanh-nghiep-59-2020-qh14', 16]]
- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q032` [right_doc_wrong_article] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `q017` [right_doc_wrong_article] Công ty tôi kinh doanh hàng hóa thuộc diện không phải chịu thuế GTGT. Thuế GTGT đầu vào có được khấu trừ hoặc đề nghị hoàn không, và trường hợp áp dụng thuế suất 0% có khác không? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 5]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q038` [right_doc_wrong_article] Công ty tôi có thể sắp xếp cho nhân viên đã vượt độ tuổi lao động làm ít giờ mỗi ngày hoặc làm bán thời gian không? -> gold [['bo-luat-lao-dong-vbhn-18-2026-vbhn-vpqh', 148]]
- `q055` [wrong_document] Tôi là cổ đông của một công ty. Tôi có thể đứng tên góp vốn thay cho người khác không? -> gold [['nghi-dinh-296-2026-nd-cp', 1]]

### sparse-s256 [dev]

- `q032` [wrong_document] Một cá nhân ở nước ngoài kinh doanh qua nền tảng số tại Việt Nam thì ai có trách nhiệm kê khai và nộp thuế, các khoản thu khác? -> gold [['luat-quan-ly-thue-108-2025-qh15', 12]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q029` [right_doc_wrong_article] Tôi là cá nhân cư trú kinh doanh. Tỷ lệ thuế tính trên doanh thu chịu thuế được xác định theo căn cứ nào? -> gold [['nghi-dinh-253-2026-nd-cp', 45]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]

### hybrid-article-cohere-pro [dev]

- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-article-cohere [dev]

- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-vbpl-cohere [dev]

- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-vbpl-full-cohere-expand [dev]

- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]

### hybrid-vbpl-full-cohere [dev]

- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]

### hybrid-vbpl [dev]

- `q026` [wrong_document] Tôi bán phần vốn góp trong một công ty, bán chứng khoán hoặc chuyển nhượng vốn theo hình thức khác thì khoản thu nào được xếp vào thu nhập chịu thuế thu nhập cá nhân? -> gold [['luat-thue-tncn-109-2025-qh15', 3]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [wrong_document] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q059` [right_doc_wrong_article] Tôi đăng ký vốn công ty cao hơn số tiền thực góp, đồng thời định giá tài sản đưa vào góp vốn cao hơn giá trị thực thì có vi phạm điều cấm nào không? -> gold [['luat-doanh-nghiep-59-2020-qh14', 16]]
- `q045` [wrong_document] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### ab-planner-off [dev]

- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `h12` [right_doc_wrong_article] Công ty TNHH có nhiều thành viên thì được phép có tối đa bao nhiêu người góp vốn? -> gold [['luat-doanh-nghiep-59-2020-qh14', 46]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### ab-planner-on [dev]

- `q045` [right_doc_wrong_article] Công ty tôi còn nợ một phần tiền bảo hiểm xã hội khi nhân viên nghỉ việc. Trong thời gian chưa thu đủ khoản nợ, công ty cần xác nhận quá trình đóng của nhân viên ra sao, và xử lý thế nào khi thu hồi được tiền? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]
- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]

### hybrid-vbpl-full-cohere-expand [dev]

- `h11` [right_doc_wrong_article] Bán hàng hóa dịch vụ thông thường thì chịu thuế giá trị gia tăng ở mức nào? -> gold [['luat-thue-gtgt-vbhn-12-2026-vbhn-vpqh', 9]]
- `q001` [wrong_document] Doanh nghiệp tôi muốn biết cơ quan nào quy định cụ thể cách xử lý hồ sơ hoàn thuế, thu hồi tiền đã hoàn và dùng tiền hoàn để bù trừ khoản nợ thuế? -> gold [['luat-quan-ly-thue-108-2025-qh15', 18]]
- `q051` [right_doc_wrong_article] Công ty điều chỉnh tăng mức lương dùng để tính bảo hiểm xã hội cho nhân viên và áp dụng mức mới cho cả những tháng trước đó. Công ty có phải nộp bù phần bảo hiểm xã hội của thời gian đã qua không? -> gold [['nghi-dinh-158-2025-nd-cp', 8]]

### hybrid-vbpl-full-cohere-expand [test]

- `q046` [right_doc_wrong_article] Doanh nghiệp tôi cần phối hợp với những bên nào để tổ chức cuộc họp người lao động, và phải tổ chức bao lâu một lần? -> gold [['nghi-dinh-145-2020-nd-cp', 47]]
- `q008` [right_doc_wrong_article] Khi doanh nghiệp đã kê khai thuế bằng một loại tiền tệ thì có được nộp thuế bằng loại tiền khác không? -> gold [['luat-quan-ly-thue-108-2025-qh15', 14]]
- `h05` [right_doc_wrong_article] Nhân viên làm trên một năm rồi nghỉ việc thì được trả khoản tiền gì thêm và tính theo cách nào? -> gold [['bo-luat-lao-dong-vbhn-18-2026-vbhn-vpqh', 46]]
