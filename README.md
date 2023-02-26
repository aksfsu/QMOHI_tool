# QMOHI: Quantitative Measures of Online Health Information #
Quantitative Measures of Online Health Information (QMOHI) is an open-source tool that provides a multi-faceted health information quality assessment of Student Health Centers (SHCs) websites of U.S. colleges and universities. 

QMOHI is designed to be used by public health administrators, researchers, and practitioners to undertake nation-wide research studies, and potentially be adopted by American College Health Association (ACHA) to extend their services to SHC websites.

This work was published in [JMIR Formative Research](https://formative.jmir.org/2022/2/e32360) [[1](#references)]. Our collaborative work that uses QMOHI to study access to contraception information on student health center websites was [published recently](https://www.contraceptionjournal.org/article/S0010-7824(22)00011-7/fulltext) [[2](#references)]. QMOHI tool and its applications to women’s health research was featured in an [SFSU News article](https://news.sfsu.edu/archive/news-story/project-explores-how-gender-income-students-impact-college-contraception-information.html) [[3](#references)].

## Installation

```Python
# Clone the repository
git clone https://github.com/aksfsu/QMOHI_tool.git

# Install all the required packages
pip install -r requirements.txt
```

One of the packages requires [Poppler](https://poppler.freedesktop.org). Make sure to download it from [their website](https://poppler.freedesktop.org) or through [homebrew](https://formulae.brew.sh/formula/poppler).

```Python
# Install using Homebrew
brew install poppler
```


## Usage

Run the following command in the `Codebase/` folder.

```
python driver.py [path to input file]
```

### QMOHI Input File

QMOHI performs a guided search of university student health centers (SHC) websites using parameters specified in the input file which uses comma-separated values (CSV) format, to find and analyze information quality metrics for a given topic. 

| Column Index | Column Name | Description |
| ----------- | ----------- | ----------- |
| A | University_name | QMOHI constructs search queries to find SHC websites of the universities given by this column. |
| B | Keywords | QMOHI searches for SHC websites that contain the keywords specified by this column. |
| C | API_keys | Google API keys. This column can be blank if column D is filled. |
| D | Paid_API_key | Paid Google API keys. This column can be blank if column C is filled. |
| E | CSE_id | Search engine ID of Google Programmable Search Engine. |
| F | Selenium_Chrome_webdriver | Absolute path to Chrome Driver. |
| G | Output_directory | Absolute path to the directory where you want the QMOHI output files to be saved. |
| H | Comparison_document | Absolute path to the file containing the comparison content for the topic of interest, based on which QMOHI calculates the similarity to SHC website contents. If this is left blank, QMOHI will auto-generate a comparison document for a given topic, which is the first keyword provided in Column B.  |
| I | Word_vector_model | Absolute path to the pre-trained word embedding model. |
| J | Sentence_extraction_margin | Number of margin sentences before and after sentences that contain keywords (anchor sentences). Anchor sentences and margin sentences are considered as topical information.  |

Please read [the documentation](https://docs.google.com/document/d/1cqgTK_7dudHliH3DktOFCkqx72IcVd75rwZJnlqVmYQ/edit?usp=sharing) for more information on the QMOHI input file.

### Google API Key

QMOHI uses [Google's Programmable Search Engine](https://developers.google.com/custom-search). Create a project and obtain an Google API key on [Google Could Console](https://console.cloud.google.com/).


### Google Programmable Search Engine 

Obtain [Search Engine ID](https://developers.google.com/custom-search/v1/overview). This ID is referred to as Custom Search Engine (CSE) ID in QMOHI.

Please see [the documentation](https://docs.google.com/document/d/1b1FpSLW9pDVb8dCTFXAdIr5tbsb-uodFfO3wz24rV54/edit#) for information on how you can opt for Programmable Search Element Paid API.

### Chrome Driver

Download Chrome Driver from [here](https://chromedriver.chromium.org/downloads). Make sure to use the version that is compatible with your Chrome browser.

### Word Vector Model

For health topics that are often in the news, we recommend [*GoogleNews-vectors-negative300.bin*](https://code.google.com/archive/p/word2vec/). For health topics that are mostly found in medical journals, we recommend *Pubmed-w2v.bin*. For more information on word embeddings, see [this article](https://towardsdatascience.com/nlp-101-word2vec-skip-gram-and-cbow-93512ee24314) for some background and then read [the paper](https://arxiv.org/pdf/1301.3781.pdf). 

## System Overview

QMOHI comprises a modular pipeline of three components: SHC website identification, information collection, and evaluation metric calculation. QMOHI requires input information such as university names and keywords of a topic of interest passed by the QMOHI input file. In the process of applying input information, users are allowed to review and update keywords by adding keywords suggested by QMOHI's helper function. In the first component, given university names are used to identify the corresponding SHC websites. SHC website homepages along with the set of input keywords act as entry points to the second component where information related to the keywords is scraped from the SHC websites. Once relevant information is obtained, the third component quantifies its quality through metrics such as readability, objectivity, polarity, coverage, similarity, and prevalence. Accessibility and recency of the information is represented by navigation and timeliness metrics, respectively. 

## Dataset

Example input and output are stored in the `Dataset/Input` and `Dataset/Output` folder, respectively. 
- An example input file is in `Dataset/Input/Input File`.
- An example comparison document for the topic *pap smear* is in `Dataset/Input/Comparison Documents`. 
- The files in `Dataset/Output` are the results where we ran QMOHI for 549 U.S. colleges and universities on July 14, Augist 14, and September 14, 2020, for 4 health topics (*condom*, *contraception*, *LARC*, and *pap smear*) and their superset.

If you want to use these datasets, please contact [us](ak@sfsu.edu) (ak@sfsu.edu).

## References

[1] [Kulkarni, A., Wong, M., Belsare, T., Shah, R., Yu Yu, D., Coskun, B., ... & Smirnova, A. (2022). Quantifying the quality of web-based health information on student health center websites using a software tool: design and development study. JMIR Formative Research, 6(2), e32360.](https://formative.jmir.org/2022/2/e32360)  
[2] [Kakar, V., Kulkarni, A., Holschuh, C., Smirnova, A., & Modrek, S. (2022). Contraception information on the websites of student health centers in the United States. Contraception, 112, 68-73.](https://www.contraceptionjournal.org/article/S0010-7824(22)00011-7/fulltext)  
[3] [SFSU News: Project explores how gender, income of students impact college contraception information](https://news.sfsu.edu/archive/news-story/project-explores-how-gender-income-students-impact-college-contraception-information.html)  

## License

