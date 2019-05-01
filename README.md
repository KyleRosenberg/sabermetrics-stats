# MLB Stat Sandbox
MLB Stat Sandbox allows anyone to perform basic exploratory research into the world of sabermetrics. The site allows you to build a stat from the ground up using simple stats from the lahman database and view how your stat compares and correlates to team wins, and either FIP or wOBA.
  
## Stats
The lahman database provides a lot of data for a lot of stats for many different aspects of baseball. For now, only the pitching and batting dataframes are available due to their simplcity. The fielding datframe was another candidate, but since the differences between positions for how players should be performing are potentially significant, I left it out. I also added FIP to the default pitching dataframe, and wOBA to the default batting dataframe, since those are two commonly discussed stats for their respective aspect of the game.
  
## Usage
The left sidebar shows the available stat for the datframe chosen from the dropdown. The user can add a stat to their stat equation by clicking the green plus button, which will add an entry to the sidebar on the right along with updating the rendered equation in the center. The right sidebar displays the stats that are actively being used by the current equation, along with a constant that is added to the end. It also has numeric inputs for each stat that allow the user to change the coefficients and exponents for the associated stat. The red minus button intuitively allows the user to remove the stat from the current equation.
  
## Video  
<a href="http://www.youtube.com/watch?feature=player_embedded&v=otgyADJT8AU
" target="_blank"><img src="http://img.youtube.com/vi/otgyADJT8AU/0.jpg" 
alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10" /></a>
