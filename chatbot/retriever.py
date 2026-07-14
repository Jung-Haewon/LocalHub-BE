import sqlite3


class Retriever:
    def __init__(self, db_path):
        self.db_path = db_path

    def retrieve(self, parsed):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # -------------------------------
        # 1차 검색 : 지역 + 카테고리 + 키워드
        # -------------------------------

        sql = """
        SELECT
            title,
            addr1,
            tel,
            content_type_id,
            first_image
        FROM locations
        WHERE 1=1
        """

        params = []

        if parsed["district"]:
            sql += " AND addr1 LIKE ?"
            params.append(f"%{parsed['district']}%")

        if parsed["contenttype"]:
            sql += " AND contenttypeid = ?"
            params.append(parsed["contenttype"])

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

        # -------------------------------
        # 2차 검색 : 결과 없으면
        # 지역 + 카테고리만 검색
        # -------------------------------

        if not rows:

            sql = """
            SELECT
                title,
                addr1,
                tel,
                content_type_id,
                first_image
            FROM locations
            WHERE 1=1
            """

            params = []

            if parsed["district"]:
                sql += " AND addr1 LIKE ?"
                params.append(f"%{parsed['district']}%")

            if parsed["contenttype"]:
                sql += " AND content_type_id = ?"
                params.append(parsed["contenttype"])

            sql += " LIMIT 10"

            cur.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]

        conn.close()

        return rows