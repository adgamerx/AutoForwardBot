echo "Cloning Repo...."
if [ -z "$BRANCH" ]
then
  echo "Cloning main branch...."
  git clone https://github.com/adgamerx/ADx-AutoForward-Bot adgamerx/ADx-AutoForward-Bot
else
  echo "Cloning $BRANCH branch...."
  git clone -b "$BRANCH" https://github.com/adgamerx/ADx-AutoForward-Bot adgamerx/ADx-AutoForward-Bot
fi
cd adgamerx/ADx-AutoForward-Bot
pip3 install -U -r requirements.txt
echo "Starting Bot...."
gunicorn app:app & python3 main.py
