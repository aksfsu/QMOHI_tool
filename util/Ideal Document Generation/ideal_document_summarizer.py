from os import makedirs
from os.path import join, dirname
from util_text_summarizer import Summarizer

CONTRACEPTION_KEYWORDS = [
    "birth",
    "control",
    "iud",
    "iuds",
    "progesterone",
    "progestin",
    "hormonal",
    "mirena",
    "skyla",
    "kyleena",
    "liletta",
    "copper",
    "paragard",
    "implant",
    "implants",
    "nexplanon",
    "injection",
    "injections",
    "shot",
    "shots",
    "depo-provera",
    "depo",
    "emergency",
    "contraception",
    "contraceptive",
    "morning",
    "b",
    "levonorgestrel",
    "ella",
    "ulipristal",
    "acetate",
    "pill",
    "pills",
    "diaphragm",
    "spermicide",
    "spermicides",
    "patch",
    "patches",
    "vaginal",
    "ring",
    "rings",
    "cervical", 
    "cap",
    "caps",
]

LARC_KEYWORDS = [
    "iud",
    "iuds",
    "progesterone",
    "progestin",
    "hormonal",
    "mirena",
    "skyla",
    "kyleena",
    "liletta",
    "copper",
    "non-hormonal",
    "paragard",
    "contraceptive",
    "implant",
    "implants",
    "nexplanon",
    "injection",
    "injections",
    "shot",
    "shots",
    "depo-provera",
    "depo",
]

MEDICATED_ABORTION_KEYWORDS = [
    "nonsurgical", "abortion",
    "surgical",
    "medical",
    "medicated",
    "medication",
    "medications",
    "mifepristone",
    "misoprostol",
    "mifeprex",
    "ru",
    "pill",
    "pills"
]

KEYWORDS = [
    CONTRACEPTION_KEYWORDS,
    LARC_KEYWORDS,
    MEDICATED_ABORTION_KEYWORDS,
    MEDICATED_ABORTION_KEYWORDS,
]

EXPERIMENTAL_TERMS = [
    "Contraception",
    "Long Acting Reversible Contraception",
    "Medicated Abortion",
    "Abortion",
    # "Accidental Injury",
    # "Broken Limbs",
    # "First Aid",
    # "Allergy",
    # "Asthma",
    # "Flu",
    # "Cold",
    # "Standard Immunizations",
    # "Vaccines",
    # "Tobacco",
    # "Alcohol",
    # "Drug Issues",
    # "Mental Health Depression",
    # "Anxiety",
    # "Stress",
    # "Time Management",
    # "Sexual Harrassment",
    # "Abuse",
    # "Assault",
    # "Violence",
    # "Body Image",
    # "Nutrition",
    # "Obesity",
    # "HIV",
    # "STD",
    # "Sexual Health",
    # "Safe Sex",
    # "Urinary Tract Infections",
]

# Get text from the text file
def get_text_from_file(file_path):
    # Open the output file
    with open(file_path, 'r') as f:
        text = f.read()
    return text

# Calculate the similarity based on the given word vector
def main():
    for i, term in enumerate(EXPERIMENTAL_TERMS):
        doc = get_text_from_file(join("./output", term + '.txt'))
        doc = Summarizer(doc).summarize(weight=0.4)

        # Export the preprocessed text
        summarized_dir = "./summarized"
        makedirs(dirname(join(summarized_dir, term + ".txt")), exist_ok=True)
        with open(join(summarized_dir, term + ".txt"), 'w') as f:
            f.write(doc)

if __name__ == "__main__":
    main()