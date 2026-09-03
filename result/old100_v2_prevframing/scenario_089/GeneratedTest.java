import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\parallelogram.png (a, score 1.00)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\parallelogram.png (a, score 1.00)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 2
        actions.sendKeys("Start").perform();   // into element created in step 2
        actions.doubleClick(cell).perform();   // element created in step 6
        actions.sendKeys("Read A").perform();   // into element created in step 6
        actions.doubleClick(cell).perform();   // element created in step 9
        actions.sendKeys("Read B").perform();   // into element created in step 9
        actions.doubleClick(cell).perform();   // element created in step 11
        actions.sendKeys("Calculate Sum as A + B").perform();   // into element created in step 11
        actions.doubleClick(cell).perform();   // element created in step 12
        actions.sendKeys("Print Sum").perform();   // into element created in step 12
        actions.doubleClick(cell).perform();   // element created in step 14
        actions.sendKeys("End").perform();   // into element created in step 14
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        driver.findElement(By.xpath("/html/body/div[1]/div[1]/a[1]")).click();
        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[14]/td[2]")).click();
        driver.findElement(By.xpath("/html/body/div[12]/table/tbody/tr[1]/td[2]")).click();
        driver.findElement(By.xpath("/html/body/div[12]/div[1]/div[2]/button[2]")).click();
        driver.findElement(By.xpath("/html/body/div[12]/div/div[3]/button[4]")).click();

        driver.quit();
    }
}