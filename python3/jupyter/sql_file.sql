select cu,stats,duration 
from mo_catalog.statement_cu 
left join system.statement_info on system.statement_info.statement_id=mo_catalog.statement_cu.statement_id 
where system.statement_info.account = 'test' 
order by cu 
desc 
limit 1000;