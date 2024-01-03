### Quickly Raise Stats Request 

- Fork the repository (https://github.com/kshitij-raj-sharma/OSMSG-stats)- Go to the OSMSG repository and click on the Fork button to create a fork of the repository under your own Github account.

- Create a new branch - After forking the repository, create a new branch for your changes. Name the branch according to the changes you're making. for eg : ```request/hashtag_name```

- Create the YAML file - Go to the ```.github/workflows``` directory in your forked repository and click on the "Create new file" button. Name the file as per the template provided in the documentation. For example, if you want to create a workflow for daily tracking of the hotosm hashtag, name the file ```daily_hotosm.yml```

- Paste Content as in [sample.yml](../sample.yml)

- Replace ```REPLACE_ME_WITH_HASHTAG``` with your ```hashtag name``` in doc , You can use Control+F to find REPLACE_ME_WITH_HASHTAG and replace in one shot with dropdown like in screenshot below
  <img width="866" alt="image" src="https://user-images.githubusercontent.com/36752999/236824979-b45db0a1-45f7-4226-b559-30c6d20a992b.png">


- Commit and push changes - After making the necessary changes to the YAML file, commit the changes and push the branch to your forked repository.

#### Create a Pull Request

- Go to the original repository - Go to the original OSMSG repository and click on the "New pull request" button.

- Select your forked repository and branch - In the "Compare changes" section, select your forked repository and the branch you created in the previous steps.

- Review changes - Review the changes you've made in the YAML file.

- Create the pull request - If everything looks good, click on the "Create pull request" button to create the pull request. Provide description about what you wanted to do , Hashtag you wanted to add its frequency in words 

- Wait for approval - Wait for the repository admins to review your changes and approve the pull request. If any changes are required, make the changes and push them to your forked repository. The pull request will automatically update with the new changes.

***Note : Don't change anything on .yml until and unless you know what you are doing***
