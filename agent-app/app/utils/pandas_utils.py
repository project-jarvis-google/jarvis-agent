import pandas as pd


def list_of_dict_to_md_table(json_arr: list, max_col_width: int = None) -> str:
    print("json_arr => ", json_arr)
    pd.set_option("display.max_colwidth", 20)
    df = pd.DataFrame.from_dict(json_arr)
    # print(df.to_markdown(index=False,tablefmt='grid',maxcolwidths=[None, max_col_width]))
    md_table_str = df.to_markdown(
        index=False, tablefmt="grid", maxcolwidths=[None, max_col_width]
    )
    print("md_table_str => ", md_table_str)
    return md_table_str


# if __name__ == "__main__":
#     test = [
#             {
#                 "language": "Java",
#                 "percentage": "iafsnouasnbfiuasnfiausfnasifunsafiunafsipunasfipunfasipunfsaifnsaipuasnpsiaujfnaspifnsafpinsafiunfipasnpfas%",
#             },
#             {
#                 "language": "Dockerfile",
#                 "percentage": ["Hello = World", "Hello = Agent"],
#             },
#         ]
#     list_of_dict_to_md_table(test, max_col_width=30)
