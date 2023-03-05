### Installation of OSMSG on Windows 

1. Install Anaconda / Miniconda on your machine 

    Documentation Link : https://docs.anaconda.com/anaconda/install/windows/ 
    
    If you already use conda env than you can skip this part 

2. Create your virtualenv with Python 3.8.16 

    Tested with ```python 3.8.16 ``` , May work on other python versions

    - You can create virtualenv with anaconda navigator GUI or From commandline itself 
        
        - Launch Anaconda Navigator , Click on Environments , Click on Create and Choose Python 3.8.16 , Nave your env and Create 
        - Search for Not installed libraries and Find Osmium-tool & Install, If not available update Channels
            https://anaconda.org/conda-forge/osmium-tool
        - Now Launch the terminal , Open Anaconda3 Promot from Start bar or click on this icon to open terminal or You can open your cmd and activate your venv with ```conda activate yourvenv_name```
        - Hit following command once promot appears
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