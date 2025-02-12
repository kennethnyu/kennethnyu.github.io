import datetime as dt
import os
import numpy as np
import pandas as pd
import sqlite3
import sys
import json
from General import Config
# Configs
r_db="src/data/databases/Snow_VoldisG1_raids_01.parquet"
p_db="src/data/databases/Snow_VoldisG1_players_01.parquet"
configs=Config()
whitelisted=configs.whitelist
spec_to_color=configs.spec_to_color
boss_order_dict=configs.boss_order_dict

# Read and clean data
raids=pd.read_parquet(r_db)[["raidId","region","timestamp"]]
players=pd.read_parquet(p_db,filters=[("class","not in",['Artist','Bard','Paladin']),
                                      ("spec","!=","Princess")]).rename(columns={"arkPassiveActive":"arkPsvActv"})
raids["serverdate"]=raids["timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x/1000)).date()).astype("str")
cols=["raidId","spec","dps","boss","difficulty","gearScore","arkPsvActv","char","isDead","serverdate"]
main_df=raids.merge(players,how="left")
main_df["char"]=main_df["name"]+" - "+main_df["region"]
main_df=main_df[main_df["char"].notnull()][cols].reset_index(drop=True)
main_df["dps"]=main_df["dps"].astype(int)
main_df["gearScore"]=main_df["gearScore"].astype(float).round(2)
main_df["arkPsvActv"]=main_df["arkPsvActv"].fillna(-1).astype(int).map({-1:"All",0:"Off",1:"On"})
main_df["boss"]=main_df["boss"].map(boss_order_dict)
# Create new final dataframe
def get_parse(dps,arr):
      return int((arr<dps).mean() * 100)
final_df=pd.DataFrame()
for i,row in main_df[["difficulty","spec"]].drop_duplicates().iterrows():
      step_df=main_df[(main_df["difficulty"]==row["difficulty"])&(main_df["spec"]==row["spec"])].reset_index(drop=True)
      # Calculate parse
      array=step_df["dps"]
      step_df["score"]=step_df["dps"].apply(lambda x: get_parse(x,array))
      final_df=pd.concat([final_df,step_df])
# Remove useless
final_df=final_df[final_df["char"].apply(lambda x: True if "#" not in x else False)].reset_index(drop=True)
# Turn to dict records style
if final_df.shape[0]>0:
      final_df.set_index("raidId").to_csv(sys.stdout)