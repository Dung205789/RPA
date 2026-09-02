import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(1) > g:nth-child(1)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Nightly timer fires").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object6 = driver.findElement(By.xpath("//not-found"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object11 = driver.findElement(By.xpath("//not-found"));
        object11.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object16 = driver.findElement(By.xpath("//not-found"));
        object16.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object21 = driver.findElement(By.xpath("//not-found"));
        object21.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object26 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object26).perform();

        actions.sendKeys("Backup complete").perform();

        WebElement object27 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(1) > g:nth-child(1)"));
        WebElement relatedObject1 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object27, 0, object27.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}