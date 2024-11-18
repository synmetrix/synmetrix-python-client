# API Reference

## Client Class

### `async def all_access_lists(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[access_lists_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[access_lists_order_by]], UnsetType] = UNSET) -> AllAccessLists`
---

### `async def sub_access_lists(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[access_lists_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[access_lists_order_by]], UnsetType] = UNSET) -> AsyncIterator[SubAccessLists]`
---

### `async def access_list(id: Any) -> AccessList`
---

### `async def update_access_list(pk_columns: access_lists_pk_columns_input, set: access_lists_set_input) -> UpdateAccessList`
---

### `async def delete_access_list(id: Any) -> DeleteAccessList`
---

### `async def create_access_list(object: access_lists_insert_input) -> CreateAccessList`
---

### `async def create_alert(object: alerts_insert_input) -> CreateAlert`
---

### `async def update_alert(pk_columns: alerts_pk_columns_input, set: alerts_set_input) -> UpdateAlert`
---

### `async def delete_alert(id: Any) -> DeleteAlert`
---

### `async def send_test_alert(delivery_config: Any = UNSET, delivery_type: str = UNSET, exploration_id: Union[Optional[Any], UnsetType], name: Union[Optional[str], UnsetType]) -> SendTestAlert`
---

### `async def set_default_branch(branch_id: Any, datasource_id: Any) -> SetDefaultBranch`
---

### `async def export_data(branch_id: Union[Optional[str], UnsetType] = UNSET) -> ExportData`
---

### `async def create_branch(object: branches_insert_input) -> CreateBranch`
---

### `async def current_user(id: Any) -> CurrentUser`
---

### `async def sub_current_user(id: Any) -> AsyncIterator[SubCurrentUser]`
---

### `async def team_data(team_id: Any) -> TeamData`
---

### `async def sub_team_data(team_id: Any) -> AsyncIterator[SubTeamData]`
---

### `async def update_user_info(user_id: Any = UNSET, display_name: Union[Optional[str], UnsetType] = UNSET, email: Union[Optional[Any], UnsetType]) -> UpdateUserInfo`
---

### `async def create_data_source(object: datasources_insert_input) -> CreateDataSource`
---

### `async def datasources(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[datasources_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[datasources_order_by]], UnsetType] = UNSET) -> Datasources`
---

### `async def all_data_sources(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[datasources_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[datasources_order_by]], UnsetType] = UNSET) -> AsyncIterator[AllDataSources]`
---

### `async def fetch_tables(id: Any) -> FetchTables`
---

### `async def fetch_meta(datasource_id: Any = UNSET, branch_id: Union[Optional[Any], UnsetType]) -> FetchMeta`
---

### `async def current_data_source(id: Any) -> CurrentDataSource`
---

### `async def update_data_source(pk_columns: datasources_pk_columns_input, set: datasources_set_input) -> UpdateDataSource`
---

### `async def check_connection(id: Any) -> CheckConnection`
---

### `async def delete_data_source(id: Any) -> DeleteDataSource`
---

### `async def gen_data_schemas(datasource_id: Any = UNSET, branch_id: Any = UNSET, tables: List[SourceTable], overwrite: Union[Optional[bool], UnsetType], format: Union[Optional[str], UnsetType]) -> GenDataSchemas`
---

### `async def run_source_sql_query(datasource_id: Any, query: str, limit: int) -> RunSourceSQLQuery`
---

### `async def create_exploration(object: explorations_insert_input) -> CreateExploration`
---

### `async def gen_sql(exploration_id: Any) -> GenSQL`
---

### `async def current_exploration(id: Any = UNSET, offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType]) -> CurrentExploration`
---

### `async def members(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[members_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[members_order_by]], UnsetType] = UNSET) -> Members`
---

### `async def update_member(pk_columns: members_pk_columns_input, set: members_set_input) -> UpdateMember`
---

### `async def update_member_role(pk_columns: member_roles_pk_columns_input, set: member_roles_set_input) -> UpdateMemberRole`
---

### `async def delete_member(id: Any) -> DeleteMember`
---

### `async def invite_member(email: str = UNSET, team_id: Any, role: Union[Optional[str], UnsetType]) -> InviteMember`
---

### `async def current_log(id: Any) -> CurrentLog`
---

### `async def all_logs(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[request_logs_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[request_logs_order_by]], UnsetType] = UNSET) -> AllLogs`
---

### `async def sub_all_logs(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[request_logs_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[request_logs_order_by]], UnsetType] = UNSET) -> AsyncIterator[SubAllLogs]`
---

### `async def create_report(object: reports_insert_input) -> CreateReport`
---

### `async def update_report(pk_columns: reports_pk_columns_input, set: reports_set_input) -> UpdateReport`
---

### `async def delete_report(id: Any) -> DeleteReport`
---

### `async def all_schemas(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[dataschemas_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[dataschemas_order_by]], UnsetType] = UNSET) -> AsyncIterator[AllSchemas]`
---

### `async def all_data_schemas(offset: Union[Optional[int], UnsetType] = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, where: Union[Optional[branches_bool_exp], UnsetType] = UNSET, order_by: Union[Optional[List[branches_order_by]], UnsetType] = UNSET) -> AllDataSchemas`
---

### `async def delete_schema(id: Any) -> DeleteSchema`
---

### `async def credentials(team_id: Any) -> Credentials`
---

### `async def sub_credentials(team_id: Any) -> AsyncIterator[SubCredentials]`
---

### `async def insert_sql_credentials(object: sql_credentials_insert_input) -> InsertSqlCredentials`
---

### `async def delete_credentials(id: Any) -> DeleteCredentials`
---

### `async def create_team(name: str) -> CreateTeam`
---

### `async def edit_team(pk_columns: teams_pk_columns_input, set: teams_set_input) -> EditTeam`
---

### `async def delete_team(id: Any) -> DeleteTeam`
---

### `async def current_team(id: Any) -> CurrentTeam`
---

### `async def get_users() -> GetUsers`
---

### `async def version_doc(id: Any) -> AsyncIterator[VersionDoc]`
---

### `async def create_version(object: versions_insert_input) -> CreateVersion`
---

### `async def version_by_branch_id(branch_id: Any = UNSET, limit: Union[Optional[int], UnsetType] = UNSET, offset: Union[Optional[int], UnsetType]) -> VersionByBranchId`
---

### `async def current_version(branch_id: Any) -> CurrentVersion`
---

### `async def versions_count(branch_id: Any) -> AsyncIterator[VersionsCount]`
---

