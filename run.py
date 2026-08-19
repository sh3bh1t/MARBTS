from collections import deque
def count_islands(grid):
    rows=len(grid)
    cols=len(grid[0])
    islands=0
    q=deque()
    dirns=[[1,0],[-1,0],[0,1],[0,-1]]
    for i in range(rows):
        for j in range(cols):
            if grid[i][j]=='1':
                islands+=1
                q.append([i,j])
                grid[i][j]='0'
                
                while q:
                    r,c = q.popleft()
                    for dr, dc in dirns:
                        row=r+dr
                        col= c+dc
                        
                        if (row in range(rows) and col in range(cols) and grid[row][col]=="1"):
                            grid[row][col]="0"
                            q.append([row,col])
    return islands

grid=[
    ["1","1","0","0"],
    ["1","0","0","1"],
    ["0","0","1","1"],
    ["0","0","0","1"]
]

print(count_islands(grid))