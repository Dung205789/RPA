import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.findElement(By.xpath("/html/body/lucid-chart-gui/lucid-full-page-application/div[1]/div/main/div[2]/main/div[2]/lucid-left-dock/div[2]/div/div/lucid-resizeable-left-panel/div/lucid-left-shapes-panel/lucid-deprecated-accordion/lucid-deprecated-accordion-panel/div/lucid-toolbox/lucid-scrollable/div/div/div[2]/lucid-tool-group/div/lucid-collapse-bar/div[3]/div/div/div/div[1]/div/lucid-tool-group-item[9]/button")).click();

        WebElement object1 = driver.findElement(By.cssSelector("//not-found"));
        object1.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        driver.switchTo().activeElement().sendKeys(Keys.ESCAPE);

        driver.findElement(By.xpath("/html/body/lucid-chart-gui/lucid-full-page-application/div[1]/div/main/div[2]/main/div[2]/lucid-left-dock/div[2]/div/div/lucid-resizeable-left-panel/div/lucid-left-shapes-panel/lucid-deprecated-accordion/lucid-deprecated-accordion-panel/div/lucid-toolbox/lucid-scrollable/div/div/div[3]/lucid-tool-group/div/lucid-collapse-bar/div[3]/div/div/div/div[1]/div/lucid-tool-group-item[1]/button")).click();

        // Kết nối bằng tọa độ: step 1 (896,288) → step 4 (896,388)
        actions.moveByOffset(896, 288)
                    .clickAndHold()
                    .moveByOffset(0, 100)
                    .release()
                    .moveByOffset(-896, -388)
                    .perform();

        WebElement object2 = driver.findElement(By.cssSelector("//not-found"));
        actions.click(object2).perform();
        actions.sendKeys(Keys.DELETE).perform();

        driver.quit();
    }
}