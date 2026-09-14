import os
import json
import sqlite3
import datetime

class ProvenanceDB:
    def __init__(self, db_path="work/provenance.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_provenance (
                asset_id TEXT PRIMARY KEY,
                map_name TEXT,
                source_asset TEXT,
                source_hash TEXT,
                object_name TEXT,
                semantic_class TEXT,
                confidence REAL,
                origin TEXT,
                generated_by TEXT,
                model TEXT,
                model_version TEXT,
                processing_step TEXT,
                material TEXT,
                collision TEXT,
                lod TEXT,
                physics TEXT,
                runtime_status TEXT,
                created_at TEXT
            )
        ''')
        self.conn.commit()

    def record_asset(self, **kwargs):
        cursor = self.conn.cursor()
        fields = [
            "asset_id", "map_name", "source_asset", "source_hash", "object_name",
            "semantic_class", "confidence", "origin", "generated_by", "model",
            "model_version", "processing_step", "material", "collision", "lod",
            "physics", "runtime_status", "created_at"
        ]
        values = []
        for f in fields:
            if f == "created_at" and "created_at" not in kwargs:
                values.append(datetime.datetime.now().isoformat())
            else:
                values.append(kwargs.get(f, "N/A"))
        
        placeholders = ",".join(["?"] * len(fields))
        col_names = ",".join(fields)
        cursor.execute(f'''
            INSERT OR REPLACE INTO asset_provenance ({col_names})
            VALUES ({placeholders})
        ''', values)
        self.conn.commit()

    def export_json(self, output_json_path):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM asset_provenance")
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        
        results = []
        for row in rows:
            results.append(dict(zip(col_names, row)))
            
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Exported provenance database ({len(results)} records) to {output_json_path}")
        return results

    def close(self):
        self.conn.close()
