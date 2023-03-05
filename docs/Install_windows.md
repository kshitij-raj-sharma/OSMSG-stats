### Installation of OSMSG on Windows 
Instructions are created using Anaconda Navigator GUI

1. Install Anaconda / Miniconda on your machine 

    Documentation Link : https://docs.anaconda.com/anaconda/install/windows/ 
    
    If you already use conda env than you can skip this part 

2. Create your virtualenv with Python 3.8.16 

    Tested with ```python 3.8.16 ``` , May work on other python versions

    - You can create virtualenv with anaconda navigator GUI or From commandline itself 
        
        - Launch Anaconda Navigator , Click on Environments , Click on Create and Choose Python 3.8.16 , Nave your env and Create 
        ![image](https://user-images.githubusercontent.com/36752999/222939899-40a5b683-04bd-4d7f-ae34-a38c3fb32977.png)

3. Install Osmium 
    
    - Click on your newly created venv 
    
    - Search for Not installed libraries and Find Osmium-tool & Install, If not available update Channels
    
    https://anaconda.org/conda-forge/osmium-tool
   ![image](https://user-images.githubusercontent.com/36752999/222939895-c98f364e-6413-47c0-8924-cecf1120f0a8.png)

4. Install Osmsg 

    Launch the terminal, Open Anaconda3 Prompt from Start bar or click on this icon to open terminal or You can open your cmd and activate your venv with ```conda activate yourvenv_name```  
        ![image](https://user-images.githubusercontent.com/36752999/222939893-f9959639-f75c-4b7d-8a59-3ecb380619df.png)

    - Hit following command once promot appears , make sure it has your virtualenv name on left corner of terminal
    ![image](https://user-images.githubusercontent.com/36752999/222939919-e4017c87-55d5-4149-b9c3-504b231d8eae.png)

    ```
    pip install osmsg
    ```
    - Navigate to your dir where you want to generate stats and start right away , see the help or follow readme for instruction
    ```
    osmsg -h 
    ```
    - For eg : Test stats for last hour
    ```
    osmsg --last_hour --changesets --charts
    ```
    ![image](https://user-images.githubusercontent.com/36752999/222940077-b5260c4b-78e2-41e7-8f63-d5267fa72859.png)
    - Once it is Done , Navigate to your dir with your Windows explorer where you produced stats you should find your desired stat files 
