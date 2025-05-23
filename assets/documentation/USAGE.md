# Python QueryGen

## How to use
Python QueryGen is for creating queries, so you should have already manipulated the .CSV to the desired data for input. You can keep old column values if you require additional criteria when making an UPDATE or DELETE query.

Run the program using command line
```python main.py```

Then hit the Load button and a file dialog will pop up. Choose the .CSV file of your liking. After loading the file, you will be able to choose which columns from the .CSV are included in the query. 
Additionally, if it is an UPDATE query, you will be able to choose columns in a second location. These columns are included in the WHERE clause of your query.

Next, you can select your query type. Once you've selected the correct query type, you can hit Generate SQL and it will put out a query in the textbox below. If you need to create additional queries, just load a .CSV again,
and everything will be cleared from the checkboxes and textbox.
