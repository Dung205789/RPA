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
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\diamond.png (a, score 0.96)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\parallelogram.png (a, score 1.00)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 2
        actions.sendKeys("Start").perform();   // into element created in step 2
        actions.doubleClick(cell).perform();   // element created in step 6
        actions.sendKeys("Process").perform();   // into element created in step 6
        actions.doubleClick(cell).perform();   // element created in step 9
        actions.sendKeys("Decision").perform();   // into element created in step 9
        actions.doubleClick(cell).perform();   // element created in step 11
        actions.sendKeys("A").perform();   // into element created in step 11
        actions.doubleClick(cell).perform();   // element created in step 14
        actions.sendKeys("Data").perform();   // into element created in step 14
        actions.doubleClick(cell).perform();   // element created in step 15
        actions.sendKeys("A").perform();   // into element created in step 15
        actions.doubleClick(cell).perform();   // element created in step 18
        actions.sendKeys("Document").perform();   // into element created in step 18
        actions.doubleClick(cell).perform();   // element created in step 20
        actions.sendKeys("End").perform();   // into element created in step 20
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step9_to_step11
        actions.sendKeys("NO").perform();   // into connector_from_step9_to_step11
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step9_to_step14
        actions.sendKeys("YES").perform();   // into connector_from_step9_to_step14
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        // click 'File' (exact-visible)
        // click 'Export as' (exact-visible)
        driver.findElement(By.xpath("/html/body/div[12]/table/tbody/tr[1]/td[2]")).click();
        // click 'Export' (exact-visible)
        // click 'Save' (exact-visible)

        driver.quit();
    }
}