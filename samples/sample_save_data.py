"""
Пример сохранения Supermarket Simulator (упрощённый, но с реальной ES3-структурой).

Ключевые поля игры:
- Progression.value.Money
- Progression.value.CurrentDay
- Progression.value.UnlockedLicenses (ID 21–47)
- Progression.value.CurrentStoreLevel / CompletedCheckoutCount
"""

SAMPLE_SAVE = {
    "Storage": {
        "__type": "SaveManager+StorageData,Assembly-CSharp",
        "value": {"Purchased": True, "StorageLevel": 1},
    },
    "Employees": {
        "__type": "SaveManager+EmployeesData,Assembly-CSharp",
        "value": {"CashiersData": [], "RestockersData": []},
    },
    "Progression": {
        "__type": "SaveManager+ProgressionContainer,Assembly-CSharp",
        "value": {
            "UnlockedLicenses": [21, 22],
            "Money": 15420.5,
            "CurrentDay": 7,
            "CompletedCheckoutCount": 42,
            "CurrentStoreLevel": 2,
            "StoreUpgradeLevel": 1,
            "StoreName": "Мой Маркет",
            "CheckoutCount": 2,
            "ShelfCount": 12,
            "EmployeeCount": 1,
            "Version": "0.9.0-sample",
        },
    },
    "Quality": {
        "__type": "SaveManager+SettingsContainer,Assembly-CSharp",
        "value": {
            "QualitySetting": 2,
            "LanguageSetting": 9,
            "FullScreen": True,
        },
    },
}
