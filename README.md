# jira-reporter

## Contributing

### Prepare repository

```
git clone https://github.com/Bondifuzz/bugtrackers-integration/jira-reporter.git
cd jira-reporter

pip install -r requirements-dev.txt

ln -s local/dotenv .env
ln -s local/docker-compose.yml docker-compose.yaml
ln -s local/elasticmq.conf elasticmq.conf

docker-compose -p jira-reporter up -d
```

Please, add credentials of your JIRA to ```local/dotenv```. If you don't have a JIRA, use its [trial version](https://support.atlassian.com/jira-service-management-cloud/docs/sign-up-for-a-jira-service-management-site/)

## Run service

To run jira-reporter service run the following commands:
```
# Terminal 1
python3 -m jira_reporter

# Terminal 2
python3 jira_reporter/producer.py
```