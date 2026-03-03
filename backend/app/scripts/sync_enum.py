from enum import Enum
import inspect
from app.models import enums

def generate_ts_enums(output_path):
    content = "// ⚠️ CE FICHIER EST GÉNÉRÉ AUTOMATIQUEMENT. NE PAS MODIFIER MANUELLEMENT.\n\n"
    
    for name, obj in inspect.getmembers(enums):
        if inspect.isclass(obj) and issubclass(obj, str) and issubclass(obj, Enum):
            content += f"export enum {name} {{\n"
            for item in obj:
                content += f"  {item.name} = '{item.value}',\n"
            content += "}\n\n"
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Enums synchronisés dans {output_path}.")

if __name__ == "__main__":
    generate_ts_enums("../frontend/src/types/generated_enums.ts")