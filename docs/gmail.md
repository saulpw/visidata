# Using Gmail with OAuth 2.0

## Why

As of May 30 2022, Google [doesn't allow](https://support.google.com/accounts/answer/6010255?hl=en) you to log into your IMAP gmail account using only a username/password combination.
So to open your Gmail in Visidata you need to create a Google API App, attach some scopes to it, generate a client ID and secret, then let Visidata use that client ID and secret (in a json file).

## How

First, go to the [Google Console](https://console.cloud.google.com/apis/dashboard)

<br/>

![](assets/gmail_oauth/1.png)

<br/>

And click `CREATE PROJECT`

---


![](assets/gmail_oauth/2.png)

Give the project a name then click `CREATE`


---

Open a new tab and go to the [API Library](https://console.cloud.google.com/apis/library)

<br/>

![](assets/gmail_oauth/enable/1.png)

Search for `gmail`

---

![](assets/gmail_oauth/enable/2.png)

Click the search result `Gmail API`

---

![](assets/gmail_oauth/enable/3.png)

Click `ENABLE`

---

Go back to your first tab

On the left, select `OAuth consent screen` 

![](assets/gmail_oauth/3.png)

Then select `External` and click `CREATE` to create an App 

---

![](assets/gmail_oauth/4.png)

Give the App a name and input your gmail address.

---

![](assets/gmail_oauth/5.png)

Click `ADD OR REMOVE SCOPES`

---

![](assets/gmail_oauth/6.png)

Search for `gmail`

---

![](assets/gmail_oauth/7.png)

Click the checkbox by the row with the scope value `https://mail.google.com/`

Then scroll to the bottom

---

![](assets/gmail_oauth/8.png)

And click `UPDATE`

---

![](assets/gmail_oauth/9.png)

You should see your selected scopes.

Click `SAVE AND CONTINUE`

---

![](assets/gmail_oauth/10.png)

Click `ADD USERS`

---

![](assets/gmail_oauth/11.png)

Type in your gmail email address then click `ADD`

---

![](assets/gmail_oauth/12.png)

On the left, click `Credentials`

---

![](assets/gmail_oauth/13.png)

Near the top click `CREATE CREDENTIALS`

Then click `OAuth client ID`

---

![](assets/gmail_oauth/14.png)

Select the application type `Desktop App` and give your OAuth 2.0 client a name then click `CREATE`

---

![](assets/gmail_oauth/15.png)

Click `DOWNLOAD JSON` and move the downloaded file into the visidata project directory at the path `vdplus/api/google/` and call the file `google-creds.json`

---

Now, on the command line run the equivalent for you:

`vd "imap://me@gmail.com@imap.gmail.com"`

Then you should get a web browser popup:

![](assets/gmail_oauth/16.png)

Select the account whose email address you have been using in these instructions.

---

![](assets/gmail_oauth/17.png)

Click `Select all`

---

![](assets/gmail_oauth/18.png)

See your gmail in Visidata.

<Chef's Kiss>

---

