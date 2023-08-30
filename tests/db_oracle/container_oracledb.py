from testcontainers.oracle import OracleDbContainer


class OracleDbContainerNoCX(OracleDbContainer):
    def get_connection_url(self):
        return super()._create_connection_url(
            dialect="oracle+oracledb", username="system", password="oracle", port=self.container_port,
            db_name="xe"
        )
