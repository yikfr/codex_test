from pymysql import Connection
import pymysql
from pymysql.converters import conversions

con = None

my_dict_mmy = {
    'host': 'localhost',
    'user': 'root',
    'password': '200712dong+-*/',
    'charset': 'utf8mb4',
    'autocommit': True
}

def mmy_connection():
    try:
        CON = pymysql.Connection(**my_dict_mmy)
        return CON
    except Exception as e:
        print(e)
        return None

def mmy_initialization():
    con = mmy_connection()
    if not con:
        return False
    try:
        with con.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS `memory` CHARACTER SET utf8mb4")
            con.select_db("memory")
            create_sql = """
            CREATE TABLE IF NOT EXISTS `memory` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `account` varchar(50) DEFAULT NULL,
            `content` varchar(50) DEFAULT NULL,
            `memory` varchar(5000) DEFAULT NULL,
            PRIMARY KEY (`id`),
            INDEX `idx_account` (`account`),
            INDEX `idx_session` (`content`)
            ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4
            """
            cursor.execute(create_sql)
            return True
    except Exception as e:
        print(e)
        return False
    finally:
        if con:
            con.close()

def save_memory(account: str, content: str, user_msg: str, ai_msg: str) -> bool:
    con = mmy_connection()
    if not con:
        return False
    try:
        con.select_db("memory")
        with con.cursor() as cursor:
            conversation = f"User: {user_msg}\nAI: {ai_msg}\n"
            check_sql = "SELECT `memory` FROM `memory` WHERE `account` = %s AND `content` = %s"
            cursor.execute(check_sql, (account, content))
            result = cursor.fetchone()
            if result:
                update_memory = result[0] + conversation
                update_sql = "UPDATE `memory` SET `memory`=%s WHERE `account`=%s AND `content`=%s"
                cursor.execute(update_sql, (update_memory, account, content))
            else:
                insert_sql = "INSERT INTO `memory` (`account`, `content`, `memory`) VALUES (%s, %s, %s)"
                cursor.execute(insert_sql, (account, content, conversation))
            return True
    except Exception as e:
        print(e)
        return False
    finally:
        if con:
            con.close()

def get_memory(account: str, content = None):
    con = mmy_connection()
    if not con:
        return False, None
    try:
        con.select_db("memory")
        with con.cursor() as cursor:
            if content:
                select_sql = "SELECT `memory` FROM `memory` WHERE `account` = %s AND `content` = %s"
                cursor.execute(select_sql, (account, content))
                result = cursor.fetchone()
                if result:
                    return True, result[0]
                else:
                    return False, None
            else:
                select_sql = "SELECT `memory` FROM `memory` WHERE `account` = %s"
                cursor.execute(select_sql, (account))
                result = cursor.fetchone()
                if result:
                    return True, result[0]
                else:
                    return False, None
    except Exception as e:
        print(e)
        return False, None
    finally:
        if con:
            con.close()

def delete_memory(account: str):
    con = mmy_connection()
    if not con:
        return False, None
    try:
        con.select_db("memory")
        with con.cursor() as cursor:
            if account:
                delete_sql = "DELETE FROM `memory` WHERE `account` = %s"
                result = cursor.execute(delete_sql,(account))
                con.commit()
                if result:
                    return True, "删除成功"
                else:
                    return False, "删除失败"
            else:
                return False, "无记忆"
    except Exception as e:
        print(e)
        return False, None
    finally:
        if con:
            con.close()



if __name__ == "__main__":
    if mmy_initialization():
        print("0")
    else:
        print("1")
        exit()
    user = "user"
    content = str("乱七八糟")
    if save_memory(user, content, "你好。", "你好！意大利面就应该拌42号混凝土。"):
        print("0")
    else:
        print("1")
    if save_memory(user, content, "啊，对对对。", "啊，对对对。"):
        print("0")
    else:
        print("1")
    success, sessions = get_memory(user, content)
    if success:
        print(f"内容: {sessions}")
        if sessions:
            first_content = sessions
            success, conversation = get_memory(user, first_content)
            if success:
                print(f"\n=== 会话 '{first_content}' 的详细内容 ===")
                print(conversation)
            else:
                print("1")
    else:
        print("1")
    if delete_memory(user):
        print("✅ 记忆删除成功")
    else:
        print("❌ 记忆删除失败（可能记录不存在）")