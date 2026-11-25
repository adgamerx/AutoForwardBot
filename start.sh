echo "Cloning Repo...."
if [ -z "$BRANCH" ]
then
  echo "Cloning main branch...."
  git clone https://github.com/adgamerx/AutoForwardBot adgamerx/AutoForwardBot
else
  echo "Cloning $BRANCH branch...."
  git clone -b "$BRANCH" https://github.com/adgamerx/AutoForwardBot adgamerx/AutoForwardBot
fi
cd adgamerx/AutoForwardBot
pip3 install -U -r requirements.txt
echo "Starting Bot...."
gunicorn app:app & python3 main.py
