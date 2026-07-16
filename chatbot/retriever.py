import sqlite3


class Retriever:
    def __init__(self, db_path):
        self.db_path = db_path

    def retrieve(self, parsed):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 검색 조건이 하나도 없으면 검색 안 함
        if (
            not parsed["district"]
            and not parsed["contenttype"]
            and not parsed["keywords"]
        ):
            conn.close()
            return []

        sql = """
        SELECT
            id,
            title,
            addr1,
            tel,
            content_type_id,
            first_image
        FROM locations
        WHERE 1=1
        """

        params = []

        # -----------------------------
        # 지역 (리스트)
        # -----------------------------
        if parsed["district"]:
            sql += " AND ("

            conditions = []

            for district in parsed["district"]:
                conditions.append("addr1 LIKE ?")
                params.append(f"%{district}%")

            sql += " OR ".join(conditions)
            sql += ")"

        # -----------------------------
        # 카테고리
        # -----------------------------
        if parsed["contenttype"]:
            sql += " AND content_type_id = ?"
            params.append(parsed["contenttype"])

        # -----------------------------
        # 키워드
        # -----------------------------
        if parsed["keywords"]:
            sql += " AND ("

            conditions = []

            for keyword in parsed["keywords"]:
                conditions.append("title LIKE ?")
                params.append(f"%{keyword}%")

                conditions.append("addr1 LIKE ?")
                params.append(f"%{keyword}%")

            sql += " OR ".join(conditions)
            sql += ")"

        sql += " LIMIT 10"

        cur.execute(sql, params)
        rows = [dict(row) for row in cur.fetchall()]

        # -------------------------------------------------
        # 키워드만 검색했는데 결과가 없으면 종료
        # -------------------------------------------------

        if (
            not rows
            and parsed["keywords"]
            and not parsed["district"]
            and not parsed["contenttype"]
        ):
            conn.close()
            return []

        # -------------------------------------------------
        # 지역 또는 카테고리가 있을 때 fallback
        # -------------------------------------------------

        if (
            not rows
            and (parsed["district"] or parsed["contenttype"])
        ):

            sql = """
            SELECT
                id,
                title,
                addr1,
                tel,
                content_type_id,
                first_image
            FROM locations
            WHERE 1=1
            """

            params = []

            # 지역 (리스트)
            if parsed["district"]:
                sql += " AND ("

                conditions = []

                for district in parsed["district"]:
                    conditions.append("addr1 LIKE ?")
                    params.append(f"%{district}%")

                sql += " OR ".join(conditions)
                sql += ")"

            # 카테고리
            if parsed["contenttype"]:
                sql += " AND content_type_id = ?"
                params.append(parsed["contenttype"])

            sql += " LIMIT 10"

            cur.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        print(self.db_path)

        cur.execute("PRAGMA table_info(locations)")
        conn.close()

        

        return rows