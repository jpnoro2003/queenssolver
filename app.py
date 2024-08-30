# Import Libraries
from ortools.linear_solver import pywraplp
import streamlit as st
import matplotlib.pyplot as plt

# A Queens is a 2D array where:
# * Each entry in each nested array ranges from 1 to n, where n is the dimension of the array
# * the array is square

def create_data_model(nested_arr):
    """
    Create dictionary with MIP model settings based on valid Queens board
    Requries: nested_arr is valid queens board
    create_data_model: Queens -> Dict
    """
    data = {}
    data["constraint_coeffs"] = [] # Coefficients for each constraint (each element is an array with 0/1)
    data["lower_bounds"] = [] # lower bound for each constraint
    data["upper_bounds"] = [] # upper bound for each constraint
    data["obj_coeffs"] = [1 for i in range(len(nested_arr)**2)] # coefficients for each constraint (each value is 1)
    data["num_vars"] = len(nested_arr)**2 # number of variables in model (number of cells in Queens board)
    data["num_constraints"] = 0 # number of constraints in model currently (will update as constraints added)
    return data

def verify(nested_arr):
    """
    For a given 2D array, verify if it is a Queens, otherwise return an error message
    verify: NestedArray -> OneOf(True, Str)
    """

    # Get dimension of board based on first row, otherwise return error for empty board
    try:
        dim = len(nested_arr[0])
    except:
        return "Error: Empty or incorrectly formatted board"
    
    # Check if number of rows is valid
    if len(nested_arr) != dim:
        return "Error: Number of rows and columns do not match"
    
    # Iterate through rows, check if each has same number of elements
    categories = []
    for row in nested_arr:
        if len(row) != dim:
            return "Error: This row does not match the dimension " + str(row)
        else:
            categories = categories + row
    
    # check if categories are valid
    categories = list(set(categories))
    if (categories[0] == 1) and (len(categories) == dim):
        return True
    else:
        return "Error: Invalid Categories"

def solve(nested_arr):
    """
    Given a nested array, determine if it is a Queens, then solve the Queens instance if possible (output shown in Streamlit)
    Effects: Outputs to Streamlit
    solve: NestedArray -> None
    """

    # if nested_arr is not Queens, print out error code and stop
    if verify(nested_arr) is not True:
        st.write(verify(nested_arr))
        return
    
    # create model based on valid Queens
    model = create_data_model(nested_arr)
    dimension = len(nested_arr)

    # category constraints: For each category, labelled 1 to n in nested_arr (where n is the dimension), we want exactly one queen placed
    for category in range(dimension):
        constraint = []
        for i in range(dimension): # iterate through rows
            for j in range(dimension): # iterate through columns
                if nested_arr[i][j] == category + 1: # if cell belongs to category, set constraint coefficient to 1 otherwise 0
                    constraint.append(1)
                else:
                    constraint.append(0)
        model["constraint_coeffs"].append(constraint)
        model["lower_bounds"].append(1)
        model["upper_bounds"].append(1)
        model["num_constraints"] = model["num_constraints"] + 1

    # row constraints: Each row has exactly one queen
    for i in range(dimension): # iterate through each row
        constraint = [0 for i in range(dimension**2)]
        for j in range(dimension): # iterate through each column in the row
            constraint[i*dimension+j] = 1
        model["constraint_coeffs"].append(constraint)
        model["lower_bounds"].append(1)
        model["upper_bounds"].append(1)
        model["num_constraints"] = model["num_constraints"] + 1

    # column constraints: Each column has exactly one queen
    for i in range(dimension): # Iterate through each column
        constraint = [0 for i in range(dimension**2)]
        for j in range(dimension): # Iterate through each row in the column
            constraint[i+dimension*j] = 1
        model["constraint_coeffs"].append(constraint)
        model["lower_bounds"].append(1)
        model["upper_bounds"].append(1)
        model["num_constraints"] = model["num_constraints"] + 1

    # closeness constraints - right diagonal (for each cell, the immediate diagonal has at most one queen - other adjacencies assured by previous constraints)
    for i in range(dimension-1): #row
        for j in range(dimension - 1): #col
            constraint = [0 for i in range(dimension**2)]
            constraint[dimension*i+j] = 1
            constraint[dimension*(i+1)+j+1] = 1
            model["constraint_coeffs"].append(constraint)
            model["lower_bounds"].append(0)
            model["upper_bounds"].append(1)
            model["num_constraints"] = model["num_constraints"] + 1

    # closeness constraints - left diagonal
    for i in range(dimension-1):
        for j in range(1,dimension):
            constraint = [0 for i in range(dimension**2)]
            constraint[dimension*i+j] = 1
            constraint[dimension*(i+1)+j-1] = 1
            model["constraint_coeffs"].append(constraint)
            model["lower_bounds"].append(0)
            model["upper_bounds"].append(1)
            model["num_constraints"] = model["num_constraints"] + 1
    
    solver = pywraplp.Solver.CreateSolver("SCIP")

    # initialize variables
    x = {}
    for j in range(model["num_vars"]):
        x[j] = solver.IntVar(0, 1, "x[%i]" % j)

    # initialize constraints
    for i in range(model["num_constraints"]):
        constraint = solver.RowConstraint(model["lower_bounds"][i], model["upper_bounds"][i], "")
        for j in range(model["num_vars"]):
            constraint.SetCoefficient(x[j], model["constraint_coeffs"][i][j])

    # Set objective
    objective = solver.Objective()
    for j in range(model["num_vars"]):
        objective.SetCoefficient(x[j], model["obj_coeffs"][j])
    objective.SetMaximization()

    # Solve
    status = solver.Solve()

    # Determine if we have a solution
    if status == pywraplp.Solver.OPTIMAL:
        sol_arr = []
        row = []
        for j in range(model["num_vars"]):     
                row.append(1 if x[j].solution_value() == 1.0 else 0)
                if len(row) == dimension:
                        sol_arr.append(row)
                        row = []
        fig, ax = plt.subplots()
        im = ax.imshow(nested_arr)
        plt.xticks([])  
        plt.yticks([])  

        for i in range(len(sol_arr)):
            for j in range(len(sol_arr)):
                text = ax.text(j, i, 'X' if sol_arr[i][j] == 1 else "",
                            ha="center", va="center")
        st.pyplot(plt.gcf())
    else:
        st.write("Invalid or impossible board")

# Set session state to determine if button is pressed
if "clicked" not in st.session_state:
    st.session_state["clicked"] = False

# Introduction 
st.title("👑 Queens Solver")

tab1, tab2, tab3 = st.tabs(["Solver", "Explanation", "Info"])
with tab1:
    st.write("This web app will solve a valid board for the Linkedin 'Queens' game!")
    st.write("Label each different group as an integer starting from one. For each row, write out the categories that appear, separating each cell with a '.' and each row with a ','")
    st.write("For example, the following input will output the following solution:")
    col1, col2 = st.columns(2)
    with col1:
        st.write("""‎ 
                
        1.2.2.3.4.4.4.5,
    1.1.2.3.3.4.4.5,
    6.1.1.1.1.4.4.5,
    6.6.1.1.1.1.4.5,
    7.7.1.1.1.1.4.1,
    8.7.1.1.1.1.1.1,
    8.8.8.1.1.1.1.1,
    8.8.8.8.8.1.1.1""")
    with col2:
        st.write("‎ ")
        st.image("Example.png", width=300)

    # Create form elements
    board = st.text_area("Enter the board below", height=5)
    inputted_board = st.button("Solve Board")

    # Run solver when button is pressed
    if inputted_board:
        board_list_raw = board.strip().split(",")
        board_list = []
        for i in board_list_raw:
            temp = [int(k) for k in i.split(".")]#[int(k) for k in list(i)] 
            board_list.append(temp)
        final = solve(board_list)
with tab2:
    lin = """https://www.linkedin.com/help/linkedin/answer/a6269510#:~:text=Rules%201%20Each%20row%2C%20column%2C%20and%20colored%20region,eliminate%20cells%20that%20cannot%20contain%20a%20Crown%20symbol."""
    st.write("Before we explain our model, we must first understand the rules of Queens. According to [LinkedIn's official rules,](%s)"%lin)
    st.write("""* Each row, column, and colored region must contain exactly one Crown symbol (Queen).            
* Crown symbols cannot be placed in adjacent cells, including diagonally.""")
    
    st.subheader("Setup")
    st.write("The inputted grid is converted into a 2D Array, where there are $n$ arrays each with $n$ integers. Each integer (starting with 1) represents a coloured tile on the board. There are checks implemented to ensure that the input is valid (square grid, proper categories, etc.)")
    st.write("We notice that for a square grid with $n$ rows, there must be exactly $n$ distinct colored regions. Let $k$ be the number of regions and $n$ be the number of rows. If $k > n$, since each row much have exactly 1 queen we can fill the $n$ rows however there will be $k-n$ regions without a queen. If $k < n$, then we fill the $k$ regions however there are $n-k$ rows without a queen. Thus, $k = n$.")
    st.write("To solve Queens, we develop a Mixed Integer Program (MIP). We define the following variables:")
    st.markdown("* Let $x_{i,j}$ represent whether a queen is placed on the square located on row $i = 1, ..., n$ and column $j = 1, ..., n$. $x_{i,j} = 1$ if there is a queen on (i,j), and is 0 otherwise")
    st.markdown("* Likewise, let $c_{i,j}$ represent which region a cell belongs to. From before, we have regions $1, ..., n$. This is given to us from the Queens board, our model will try and solve for $x_{i,j}$.")

    st.subheader("Objective Function")
    st.write("For Queens, we are interested in the values of $x_{i,j}$. Thus, we will set the objective function to:")
    st.latex("""{maximize: }\sum^{n}_{i=1}\sum^{n}_{j=1}x_{i,j}""")
    st.write("We note that for a valid Queens solution, we have an objective value of n")

    st.subheader("Region Constraint")
    st.write("For each region, we want exactly one queen. Let $r = 1, ..., n$ represent the possible regions. We then have the constraint:")
    st.latex("""\sum_{c_{i,j}=r}x_{i,j} = 1 \quad ∀ r = 1,...,n""")

    st.subheader("Column Constraint")
    st.write("For each column, we want exactly one queen. This gives us the Constraint:")
    st.latex("""\sum_{i=1}^{n}x_{i,j} = 1 \quad ∀ j = 1,...,n""")

    st.subheader("Row Constraint")
    st.write("For each row, we want exactly one queen. This gives us the constraint:")
    st.latex("""\sum_{j=1}^{n}x_{i,j} = 1 \quad ∀ i = 1,...,n""")

    st.subheader("Adjacency Constraints")
    col3, col4 = st.columns(2)
    with col3:
        st.image("adjacency.png", width=340)
    with col4:
        st.write("We note that no two queens can be placed on adjacent squares, either vertically, horizontally and diagonally. Our row (Blue) and column (Green) constraints handle horizontal and vertical adjacency respectively.")
    st.write("We now need to add constraints to check if the cells in red have a queen (diagonal). We note that two cells that are diagonally adjacent can have at most one queen, otherwise our adjacency constraint is violated.")
    st.write("We will first check the bottom left diagonal for a cell. Consider cell $(i,j)$, where $i = 2, ..., n$ and $j = 1, ..., n-1$. The bottom left cell is located at $(i-1, j+1)$. This gives us the constraint:")
    st.latex("""x_{i,j}+x_{i-1,j+1} \le 1 \quad ∀ i = 2, ..., n \quad j = 1, ..., n-1""")
    st.write("We now check the bottom right diagonal for a cell. Consider cell $(i,j)$, where $i = 1, ..., n-1$ and $j = 1, ..., n-1$. The bottom left cell is located at $(i+1, j+1)$. This gives us the constraint:")
    st.latex("""x_{i,j}+x_{i+1,j+1} \le 1 \quad ∀ i = 1, ..., n-1 \quad j = 1, ..., n-1""")

    st.subheader("Final MIP")
    st.latex("""{max: }\sum^{n}_{i=1}\sum^{n}_{j=1}x_{i,j}""")
    st.latex("""{S.T.: }\sum_{c_{i,j}=r}x_{i,j} = 1 \quad ∀ r = 1,...,n""")
    st.latex("""\sum_{i=1}^{n}x_{i,j} = 1 \quad ∀ j = 1,...,n""")
    st.latex("""\sum_{j=1}^{n}x_{i,j} = 1 \quad ∀ i = 1,...,n""")
    st.latex("""x_{i,j}+x_{i-1,j+1} \le 1 \quad ∀ i = 2, ..., n \quad j = 1, ..., n-1""")
    st.latex("""x_{i,j}+x_{i+1,j+1} \le 1 \quad ∀ i = 1, ..., n-1 \quad j = 1, ..., n-1""")
    st.latex("""x_{i,j} \in \{0,1\} \quad ∀ i = 1, ..., n \quad j = 1, ..., n""")

with tab3:
    lin2 = """https://www.linkedin.com/in/jaden-noronha/"""
    st.write("Tool created by Jaden Noronha. [LinkedIn](%s)"%lin2)



# 12234445,11233445,61111445,66111145,77111141,87111111,88811111,88888111
# 1.2.2.3.4.4.4.5,1.1.2.3.3.4.4.5,6.1.1.1.1.4.4.5,6.6.1.1.1.1.4.5,7.7.1.1.1.1.4.1,8.7.1.1.1.1.1.1,8.8.8.1.1.1.1.1,8.8.8.8.8.1.1.1