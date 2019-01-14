from tinydb import TinyDB, Query

opt_in_DB = TinyDB("opt-in")
new_users = ['throwaway_the_fourth', 'DragonGodGrapha', 'ThatguyIncognito', 'DeadWater27', 'TheSpookiestUser', 'PM_ME_NBSP', 'Sardond', 'Beefsteak_Tomato', 'ihatefuckingwork', 'VampyricDanny14', 'MasterofLinking']

for username in new_users:
    opt_in_DB.insert({'username': username})
